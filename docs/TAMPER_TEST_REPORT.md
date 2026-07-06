# Tamper Test Report — Issue #26

**Date:** June 29, 2026
**Tester:** Harish (Security & Integration Lead)
**Test Location:** `tests/integration_test.py` -> `test_one_byte_tamper_rejection()`

---

## Objective

Prove that the system correctly rejects firmware that has been tampered with
during transit — even when only a **single byte** has been changed — and that
the rejection is logged as a CRITICAL security incident.

---

## Method

1. Generated a real RSA-2048 key pair.
2. Created a firmware payload and signed its SHA-256 hash with the private key
   (a genuinely valid, correctly signed bundle).
3. Flipped exactly **one byte** (index 10) in the firmware payload — simulating
   an attacker intercepting and modifying the update in transit.
4. Ran the tampered payload through the **same two-layer verification logic**
   used by the real edge agent (`edge-agent/agent.py`):
   - **Layer 1:** Recompute SHA-256 hash, compare to original.
   - **Layer 2:** Verify the original digital signature against the new
     (tampered) hash.
5. Confirmed the failure path calls `edge-agent/incident_logger.py` and
   produces a `CRITICAL`-level incident record.

---

## Result

| Step | Outcome |
|------|---------|
| Valid signed bundle created | PASS |
| One byte modified in firmware | PASS |
| Hash mismatch detected (Layer 1) | PASS — tampered hash != original hash |
| Signature rejected (Layer 2) | PASS — `InvalidSignature` raised correctly |
| CRITICAL incident logged | PASS — incident written to `edge-agent/logs/` |

**Conclusion:** A single-byte change anywhere in the firmware is sufficient to
trigger rejection at both verification layers. The agent never reaches the
`APPLYING` state for tampered data — it transitions directly to `FAULT` and
produces an auditable, timestamped incident record. No partial installs are
possible.

---

## How to Reproduce

```bash
python tests/integration_test.py
```

Look for section `[5] One-Byte Tamper Test (Issue #26)` in the output, and
check `edge-agent/logs/` for the generated incident JSON file afterward.
