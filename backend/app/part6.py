"""
Adaptive Decoy‑State BB84 simulator
----------------------------------
• Signal pulses (µ≈0.6) and decoy pulses (µ≈0.1) travel through the SAME
  honest channel, so their yields are (statistically) equal when no Eve.

• A photon‑number‑splitting (PNS) attacker blocks many decoys but lets
  signals through → yield gap ΔY triggers abort even if QBER is low.

Return tuple:
    (success: bool,
     qber   : float,
     key_or_msg: bytes|str,
     yield_signal: float,
     yield_decoy: float)
Only dependency: numpy
"""

from __future__ import annotations
import numpy as np, hashlib, secrets

# --------------------------------------------------------------------
# Tunable parameters
# --------------------------------------------------------------------
QBER_LIMIT  = 0.11      # abort if QBER exceeds 11 %
DELTA_Y_LIM = 0.05      # abort if |Ysig − Ydec| > 5 %
SAMPLE_FRAC = 0.02      # 2 % of sifted bits are disclosed
ETA         = 0.25      # overall channel+detector efficiency
PNS_DROP    = 0.6       # Eve blocks this fraction of detected decoys
rng         = np.random.default_rng()

# --------------------------------------------------------------------
# Helper: toy reconciliation + privacy amplification
# --------------------------------------------------------------------
def _reconcile(bits_a: np.ndarray, bits_b: np.ndarray) -> bytes:
    """Parity fix + drop mismatches, then SHA3‑256 hash."""
    # single parity correction
    if (bits_a.sum() - bits_b.sum()) % 2:
        bits_b[0] ^= 1
    # discard any residual mismatches
    mask = bits_a == bits_b
    aligned = bits_a[mask]
    return hashlib.sha3_256(aligned.tobytes()).digest()  # 256‑bit key


# --------------------------------------------------------------------
# Main simulation function
# --------------------------------------------------------------------
def run_bb84(n_qubits=10_000, p_noise=0.01, pns=False):
    """Simulate one session of decoy‑state BB84."""
    # 1) Alice
    bits_A   = rng.integers(0, 2, n_qubits, dtype=np.uint8)
    bases_A  = rng.integers(0, 2, n_qubits, dtype=np.uint8)   # 0=+, 1=×
    is_decoy = rng.random(n_qubits) < 0.25                    # 25 % decoy tag

    # 2) Honest channel — uniform detection probability ETA
    detection = rng.random(n_qubits) < ETA

    # 3) Optional PNS attacker
    if pns:
        # Eve blocks a portion of decoys *after* she detects multi‑photon pulses
        block = is_decoy & detection & (rng.random(n_qubits) < PNS_DROP)
        detection[block] = False            # Bob never sees these decoys
        # PNS does NOT introduce bit‑errors; it changes yields
    # disturbance array not needed anymore

    # 4) Bob chooses bases and measures
    bases_B  = rng.integers(0, 2, n_qubits, dtype=np.uint8)
    same     = bases_A == bases_B
    noise_flip = rng.random(n_qubits) < p_noise
    bits_B  = rng.integers(0, 2, n_qubits, dtype=np.uint8)
    bits_B[same] = bits_A[same] ^ noise_flip[same]

    # 5) Sifting
    sift_A = bits_A[same]; sift_B = bits_B[same]
    sig_mask   = same & (~is_decoy)
    decoy_mask = same & is_decoy
    y_sig  = detection[sig_mask].mean()  if sig_mask.any()   else 0.0
    y_dec  = detection[decoy_mask].mean() if decoy_mask.any() else 0.0

    # 6) QBER sampling
    sample_len = max(1, int(len(sift_A) * SAMPLE_FRAC))
    idx = rng.choice(len(sift_A), sample_len, replace=False)
    qber = float((sift_A[idx] != sift_B[idx]).mean())
    if qber > QBER_LIMIT:
        return False, qber, "Abort: QBER too high", y_sig, y_dec

    # 7) Decoy‑state yield gap test
    delta_y = abs(y_sig - y_dec)
    if delta_y > DELTA_Y_LIM:
        msg = f"Abort: decoy‑state anomaly (ΔY={delta_y:.3f})"
        return False, qber, msg, y_sig, y_dec

    # 8) Reconciliation + privacy amplification
    keep = np.ones(len(sift_A), bool); keep[idx] = False
    key_bytes = _reconcile(sift_A[keep], sift_B[keep])
    return True, qber, key_bytes, y_sig, y_dec


# --------------------------------------------------------------------
# CLI test
# --------------------------------------------------------------------
if __name__ == "__main__":
    ok,q,key,ys,yd = run_bb84(pns=False)
    print("Normal session →", "OK" if ok else "ABORT",
          "QBER", q, "ΔY", ys-yd)
    ok,q,msg,ys,yd = run_bb84(pns=True)
    print("PNS attack     →", "OK" if ok else "ABORT",
          "QBER", q, "ΔY", ys-yd, msg if not ok else "")
