##############################################################################
# dashboard.py  –  HybridNet + Adaptive Decoy‑State BB84 demo
##############################################################################

import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import random, hashlib
from sklearn.linear_model import LogisticRegression

# ─────────── Backend imports from your repo ─────────────────────────
from backend.app.network_builder import build_hybrid_graph
from backend.app.simulator      import simulate_path_quantum, simulate_path_classical
from backend.app.routing        import send_message_reliable
from backend.policy_registry    import POLICIES
from backend.app.part6     import run_bb84   # ⟵ new module created earlier

# ─────────── Streamlit page selector ────────────────────────────────
st.set_page_config(page_title="HybridNet • QKD Demo", layout="wide")
page = st.sidebar.radio("Page", ["Network Simulator", "QKD Demo"])

##############################################################################
# ======================  PAGE 1 – NETWORK SIMULATOR  =======================
##############################################################################
if page == "Network Simulator":
    st.title("SimQ.AI")

    # ----- sidebar controls -------------------------------------------------
    num_nodes        = st.sidebar.number_input("Number of nodes", 10, 500, 50, 10)
    quantum_ratio    = st.sidebar.slider("Quantum node ratio", 0.1, 0.9, 0.4, 0.05)
    coherence_length = st.sidebar.slider("Coherence length L (km)", 10, 200, 50, 10)
    trials           = st.sidebar.number_input("Monte‑Carlo trials per size", 50, 1000, 300, 50)
    show_topology    = st.sidebar.checkbox("Show topology preview", True)
    src_node         = st.sidebar.selectbox("Source node", list(range(num_nodes)), 0)
    dst_node         = st.sidebar.selectbox("Destination node", list(range(num_nodes)), 1)

    # ----- helper (cached) --------------------------------------------------
    @st.cache_data(show_spinner=False)
    def run_size_sweep(sizes, qratio, L, trials):
        q_rates, c_rates, hop_avgs, cost_avgs, util_q = [], [], [], [], []
        rng = random.Random(42)
        for n in sizes:
            G = build_hybrid_graph(n, qratio, seed=42)
            sq=sc=th=tc=tqe=te=cnt=0
            for _ in range(trials):
                s,d=rng.sample(list(G.nodes),2)
                if not nx.has_path(G,s,d): continue
                path = nx.shortest_path(G,s,d); cnt+=1; th+=len(path)-1
                for u,v in zip(path,path[1:]):
                    dt=G.edges[u,v]; te+=1; tqe+=dt["quantum"]
                    tc+=1+dt["distance_km"]*0.005+(dt["distance_km"]/L if dt["quantum"] else 0)
                sq+=simulate_path_quantum(G,path)["success"]
                sc+=simulate_path_classical(G,path)["success"]
            q_rates.append(sq/cnt); c_rates.append(sc/cnt)
            hop_avgs.append(th/cnt); cost_avgs.append(tc/cnt)
            util_q.append(tqe/te if te else 0)
        return q_rates,c_rates,hop_avgs,cost_avgs,util_q

    # ----- draw preview -----------------------------------------------------
    G_demo = build_hybrid_graph(num_nodes, quantum_ratio, seed=99)
    if show_topology:
        with st.expander("🔍 Topology preview", True):
            pos=nx.spring_layout(G_demo,seed=123)
            fig,ax=plt.subplots(figsize=(5,5))
            nc=["#8E7BF1" if G_demo.nodes[n]["quantum"] else "#C4C4C4" for n in G_demo]
            ec=["#FF6B00" if d["quantum"] else "#999999" for _,_,d in G_demo.edges(data=True)]
            nx.draw_networkx_nodes(G_demo,pos,node_color=nc,node_size=420,ax=ax)
            nx.draw_networkx_edges(G_demo,pos,edge_color=ec,width=1.6,ax=ax)
            nx.draw_networkx_labels(G_demo,pos,labels={n:str(n) for n in G_demo},
                                    font_size=9,font_color="white",font_weight="bold",ax=ax)
            ax.set_axis_off(); st.pyplot(fig,use_container_width=True)

    # ----- scalability charts ----------------------------------------------
    sizes=[10,50,100,200]
    qr,cr,hops,cost,util = run_size_sweep(sizes, quantum_ratio, coherence_length, trials)

    col1,col2 = st.columns(2)
    with col1:
        st.subheader("Success probability vs size")
        fig,ax=plt.subplots(); ax.plot(sizes,qr,"o-",label="Quantum")
        ax.plot(sizes,cr,"s-",label="Classical"); ax.grid(); ax.legend(); st.pyplot(fig)
    with col2:
        st.subheader("Avg hops vs size")
        fig2,ax2=plt.subplots(); ax2.plot(sizes,hops,"d-",label="Hops"); ax2.grid(); ax2.legend(); st.pyplot(fig2)

    col3,col4 = st.columns(2)
    with col3:
        st.subheader("Quantum‑edge utilisation")
        fig3,ax3=plt.subplots(); ax3.plot(sizes,util,"^-",color="tab:purple"); ax3.grid(); st.pyplot(fig3)
    with col4:
        st.subheader("Composite cost vs size")
        fig4,ax4=plt.subplots(); ax4.plot(sizes,cost,"o-",color="tab:red"); ax4.grid(); st.pyplot(fig4)
    
        # ----- auto analysis --------------------------------------------------
    def auto_analysis():
        q_drop = (qr[0] - qr[-1]) / qr[0] * 100
        hops_up = hops[-1] - hops[0]
        cost_up = cost[-1] - cost[0]
        util_ch = util[-1] - util[0]
        lines = [
            f"* Quantum success drops **{q_drop:.1f}%** from 10→200 nodes.",
            f"* Classical success stays ~flat.",
            f"* Avg hops increase by **{hops_up:+.2f}**.",
            f"* Composite cost rises by **{cost_up:+.2f}** (latency + decoherence).",
            f"* Quantum‑edge utilisation changes **{util_ch:+.2%}**.",
        ]
        return "\n".join(lines)

    st.markdown("### Technical Insights  \n" + auto_analysis())


    # ----- routing demo ----------------------------------------------------
    st.divider(); st.subheader("One‑shot reliable routing demo")
    if src_node==dst_node:
        st.warning("Source and destination must differ.")
    else:
        policy = st.selectbox("Policy", sorted(POLICIES.keys()),
                              index=sorted(POLICIES.keys()).index("hybrid"))
        result = send_message_reliable(G_demo, src_node, dst_node, policy=policy)
        st.json(result)

        # ----- LLM co‑pilot -------------------------------------------------
    st.sidebar.divider()
    st.sidebar.subheader("LLM Routing Co‑pilot")
    llm_prompt = st.sidebar.text_area("Describe a custom policy", height=100,
                                      placeholder="e.g. Prefer paths with ≥70 % quantum links")
    llm_name   = st.sidebar.text_input("Function name", "llm_policy")
    if st.sidebar.button("Generate via LLM 🚀") and llm_prompt.strip():
        from backend.app.llm_policy_builder import create_policy_from_prompt
        fn, ok = create_policy_from_prompt(llm_prompt, name=llm_name)
        st.sidebar.success(f"Policy **{llm_name}** {'added' if ok else 'fallback'}")


##############################################################################
# =======================  PAGE 2 – QKD DEMO  ===========================
##############################################################################
else:
    st.title("🔑 Adaptive Decoy‑State BB84 – Live Demo")

    # ----- sidebar parameters ----------------------------------------------
    n_qubits = st.sidebar.slider("Qubits per session", 1000, 20000, 10000, 1000)
    p_noise  = st.sidebar.slider("Channel / detector noise", 0.0, 0.15, 0.01, 0.005)

    # ----- session state for ML gauge --------------------------------------
    st.session_state.setdefault("ds_X", [])   # features [QBER, Δyield]
    st.session_state.setdefault("ds_y", [])   # labels 0=ok 1=eavesdrop
    st.session_state.setdefault("clf", None)

    def run_and_record(pns=False):
        ok,q,key_or_msg,ys,yd = run_bb84(n_qubits, p_noise, pns)
        delta = ys - yd
        st.session_state.ds_X.append([q, delta])
        st.session_state.ds_y.append(0 if ok else 1)
        # train when ≥5 samples
        y_vals = st.session_state.ds_y
        if len(y_vals) >= 5 and 0 in y_vals and 1 in y_vals:
            clf = LogisticRegression().fit(st.session_state.ds_X, y_vals)
            st.session_state.clf = clf

        return ok,q,key_or_msg,delta

    colA,colB = st.columns(2)

    # ----- normal session button -------------------------------------------
    with colA:
        if st.button("Run normal session"):
            ok,q,out,delta = run_and_record(False)
            st.write(f"QBER = **{q:.2%}**   ΔYield = **{delta:+.3f}**")
            if ok: st.success("Key: "+out.hex()[:32]+"…")
            else : st.error(out)

    # ----- PNS attack button ------------------------------------------------
    with colB:
        if st.button("☠️ PNS attack (steal photons)"):
            ok,q,out,delta = run_and_record(True)
            st.write(f"QBER = **{q:.2%}**   ΔYield = **{delta:+.3f}**")
            st.error(out)

    # ----- ML Eve probability gauge ----------------------------------------
    if st.session_state.clf and 'q' in locals():
        prob = st.session_state.clf.predict_proba([[q, delta]])[0,1]
        st.metric("ML‑estimated P(Eve)", f"{prob*100:.1f}%")