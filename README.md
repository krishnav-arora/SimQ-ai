# SimQ.ai 🧠🔗

**A browser-based hybrid quantum-classical network simulator.**  
Design, simulate, and secure next-generation quantum networks—no lab hardware required.

---

## 🚀 Overview

**SimQ.ai** (nicknamed *Bleep Bloop*) is an interactive platform to simulate how quantum and classical data can coexist in future internet infrastructure.  
It lets users build hybrid topologies, run BB84 quantum key distribution with decoy states, optimize repeater placement, and even auto-generate routing policies using natural language and LLMs.

Whether you're a researcher, student, or curious builder—this app brings quantum networking to your fingertips.

---

## 🧩 Key Features

| Feature | Description |
|--------|-------------|
| 🔧 **Topology Builder** | Create networks with 10–500 nodes, choose quantum node ratios |
| ⚛️ **Link Physics** | Simulate decoherence on quantum hops, classical latency |
| 🧭 **Hybrid Routing** | Quantum-first fallback routing from failure points |
| 📈 **Scalability Dashboard** | Auto-plots success, cost, hops, and quantum-utilization |
| 📡 **Repeater Optimizer** | Hill-climbing agent places ≤3 repeaters for best performance |
| 🔐 **BB84 + Decoy-State QKD** | Simulate secure key exchange with live PNS attack detection |
| 🧠 **ML Eve Gauge** | Logistic regression shows probability of eavesdropping in real-time |
| 🧑‍💻 **LLM Co-pilot** | Convert natural language ideas into Python routing logic |
| 💡 **Auto Insights** | Auto-explains slope changes in plots to enhance understanding |

---


## ⚙️ Tech Stack

- Python 3.10
- Streamlit (Frontend + Backend)
- NetworkX (Graph engine)
- NumPy (Monte Carlo decoherence simulation)
- scikit-learn (Lightweight ML model)
- Ollama (LLM for co-pilot)
- SHA-3 / HMAC / AES-GCM (Post-quantum crypto-safe primitives)




