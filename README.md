# Secure OTA Firmware Update Infrastructure
**Infotact Cybersecurity Internship — Project 1**

## Project Overview
A secure Over-the-Air (OTA) firmware update system for IoT cargo tracking devices. The system ensures firmware integrity and authenticity using cryptographic signing and verification before any update is installed on an edge device.

---

## Team
| Member | Role | Component |
|--------|------|-----------|
| Harish (Lead) | CI/CD & Integration | `.github/workflows/`, integration testing |
| Member 2 | Backend / DevOps | `server/`, GitHub Actions pipeline |
| Member 3 | Cryptography | `crypto/`, signing scripts |
| Member 4 | Edge Agent / QA | `edge-agent/`, rollback, documentation |

---

## Repository Structure
```
.github/workflows/     # CI/CD pipeline (GitHub Actions)
crypto/                # Key generation, hashing, signing scripts
docs/                  # Architecture, threat model documentation
edge-agent/            # Simulated IoT device verification agent
metadata/              # Firmware bundle metadata schema
server/                # Mock OTA distribution server
signer.py              # Core firmware signing script
.gitignore             # Blocks private keys and sensitive files
```

---

## Week-by-Week Progress
| Week | Focus | Status |
|------|-------|--------|
| Week 1 | PKI Setup, Hashing, Environment | ✅ In Progress |
| Week 2 | CI/CD Automated Signing | 🔜 Upcoming |
| Week 3 | Edge Device Verification Agent | 🔜 Upcoming |
| Week 4 | Anti-Rollback + Documentation | 🔜 Upcoming |

---

## Setup Instructions

### Prerequisites
```bash
pip install cryptography flask
```

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

### Run Mock Server
```bash
python server/mock_server.py
```

---

## Security Notes
- Private keys are **never** stored in this repository
- All sensitive files blocked via `.gitignore`
- Keys injected via GitHub Secrets in CI/CD pipeline
- See `docs/THREAT_MODEL.md` for full security analysis
