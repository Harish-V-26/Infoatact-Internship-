# Secure OTA Firmware Update Infrastructure
**Infotact Cybersecurity Internship — Project 1**

## Project Overview
A secure Over-the-Air (OTA) firmware update system for IoT cargo tracking devices. The system ensures firmware integrity and authenticity using cryptographic signing and verification before any update is installed on an edge device.

---

## Team
| Member | Role | Component |
|--------|------|-----------|
| Harish (Lead) | Security & Integration | `.github/workflows/`, `tests/`, `docs/` |
| Jagadesh | Backend / DevOps | `server/` — auth, rate limiting, manifest, version registry |
| Sourish | Cryptography | `crypto/` — key generation, hashing, CryptoEngine (RSA + ECDSA) |
| Rishi | Edge Agent / QA | `edge-agent/` — state machine, downloader, incident logging |

---

## Repository Structure
```
.github/workflows/     # CI/CD pipeline (GitHub Actions) — auto signs on tag push
crypto/                # Key generation, hashing, CryptoEngine, signing scripts
docs/                  # Architecture, threat model, tamper test report
edge-agent/            # Edge device agent — state machine + verification
metadata/              # Firmware bundle metadata schema
server/                # OTA distribution server — auth, manifest, registry
tests/                 # Integration, malicious actor, end-to-end demo scripts
start_all.py           # One-command launcher — server + sign + agent
.gitignore             # Blocks private keys and sensitive files
```

---

## Week-by-Week Progress
| Week | Focus | Status |
|------|-------|--------|
| Week 1 | PKI Setup, Hashing, Environment | ✅ Done |
| Week 2 | CI/CD Automated Signing | ✅ Done |
| Week 3 | Edge Device Verification Agent | ✅ Done |
| Week 4 | Anti-Rollback + Final Documentation | 🔄 In Progress |

---

## Quick Start — One Command

```bash
pip install cryptography flask requests
python start_all.py
```

This starts the server, generates keys, signs firmware, and runs the real edge agent end to end.

---

## Manual Setup

### Generate Key Pair
```bash
python crypto/keygen.py
# Saves private_key.pem locally (NEVER commit)
# Saves crypto/public_key.pem to repo (safe)
```

### Hash Firmware
```bash
python crypto/hasher.py -f edge-agent/dummy_firmware.bin
```

### Sign Firmware
```bash
python edge-agent/sign_helper.py -k private_key.pem --hash <hash_from_above> -o firmware.sig
```

### Run the Server
```bash
python server/app.py
```

---

## Running the Tests

```bash
python tests/integration_test.py        # crypto + one-byte tamper test
python tests/malicious_actor_test.py    # auth bypass, rollback, tamper attacks
python tests/end_to_end_demo.py         # full sign -> upload -> download -> verify
```

---

## Security Notes
- Private keys are **never** stored in this repository
- All sensitive files blocked via `.gitignore`
- Keys injected via GitHub Secrets in CI/CD pipeline
- Every push is scanned for accidentally exposed secrets
- See `docs/THREAT_MODEL.md` and `docs/TAMPER_TEST_REPORT.md` for full security analysis
