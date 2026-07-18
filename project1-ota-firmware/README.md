# Project 1: Secure OTA Firmware Update & Code Signing Infrastructure

**Infotact Internship — Cybersecurity Track — Month 1**
**Team:** Harish (Team Lead / Security & Integration), Jagadesh (Backend & DevOps), Sourish (Cryptography), Rishi (Edge Agent & QA)

---

## Overview

IoT cargo tracking devices receive firmware updates Over-the-Air (OTA). This project implements a zero-trust OTA pipeline: every firmware update is cryptographically signed on the server side, and independently verified on the edge device before installation. Tampered, unsigned, or downgraded (rollback) firmware is rejected automatically.

## Architecture

```
CONTROL PLANE (Server)                    DATA PLANE (IoT Device)
Developer pushes tagged release    ->     Edge Agent polls server
GitHub Actions signs firmware             Downloads firmware + signature
  (SHA-256 hash + private key)            Verifies signature with public key
Bundles firmware + .sig + metadata        Checks version against anti-rollback log
Uploads to distribution server            Installs only if all checks pass
```

Full details: [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)

## Folder Structure

| Folder | Purpose | Owner |
|---|---|---|
| `crypto/` | Key generation, hashing, signing utilities | Sourish |
| `server/` | Distribution server, manifest, version registry, auth | Jagadesh |
| `edge-agent/` | Simulated IoT device: verification, anti-rollback, incident logging | Rishi |
| `.github/workflows/` | CI/CD pipeline (validate -> sign -> distribute) + secret scanner | Jagadesh |
| `docs/` | Architecture, security report, threat model, tamper test report | Harish |
| `tests/` | End-to-end, malicious actor, and integration tests | Rishi / Harish |
| `metadata/` | Firmware version and signing metadata | Sourish |

## Key Features

- **Cryptographic signing pipeline** — RSA/ECDSA key pairs, SHA-256 hashing, keys injected via GitHub Secrets (never hardcoded)
- **CI/CD automation** — GitHub Actions triggers on release tag: validate -> sign -> distribute
- **Edge verification agent** — downloads firmware, verifies hash + signature, rejects on mismatch
- **Anti-rollback protection** — version + timestamp checks prevent downgrade attacks
- **Incident logging** — all rejected/tampered updates are logged for audit

## Running Locally

```bash
pip install -r requirements.txt
python start_all.py
```

This launches the signing server and edge agent simulation together.

## Test Results

All test suites (end-to-end, malicious actor, integration) passing at last check. See [`docs/TAMPER_TEST_REPORT.md`](./docs/TAMPER_TEST_REPORT.md) and [`docs/SECURITY_REPORT.md`](./docs/SECURITY_REPORT.md) for full results and attack scenario coverage.

## Status

Final Review submission — Week 4 complete. See [`docs/SECURITY_REPORT.md`](./docs/SECURITY_REPORT.md) for the full executive summary.
