# System Architecture — Secure OTA Firmware Update

**Owner:** Harish (Security & Integration Lead)
**Project:** Infotact Internship — Project 1: Logistics & IoT Edge

---

## High-Level Data Flow

```
CONTROL PLANE (Server Side)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Developer pushes code + release tag to GitHub
        |
        v
GitHub Actions triggers on tag (e.g. v1.0.0)
        |
        v
Pulls PRIVATE_KEY from GitHub Secrets (encrypted)
        |
        v
Hashes firmware.bin with SHA-256
        |
        v
Signs hash with Private Key -> .sig file
        |
        v
Bundles: firmware.bin + .sig + metadata.json
        |
        v
Uploads bundle to Distribution Server

DATA PLANE (IoT Device Side)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Edge Agent polls server for new update
        |
        v
Downloads metadata.json -> checks version (anti-rollback)
        |
        v
Downloads firmware.bin + .sig
        |
        v
Recalculates SHA-256 hash -> compare with metadata.hash
        |
        v
Verifies .sig using embedded Public Key
        |
        v
Pass -> Mock install + version update
Fail -> CRITICAL alert + discard bundle
```

---

## Edge Agent State Machine

```
IDLE -> DOWNLOADING -> VERIFYING -> APPLYING -> INSTALLED
                           |
                           v (on failure)
                       REJECTED + ALERT LOG
```

---

## Component Ownership

| Member | Role | Owns |
|--------|------|------|
| Harish | Security & Integration Lead | Repo structure, metadata, threat model, integration tests, security report |
| Jagadesh | Backend / DevOps | Distribution server, GitHub Actions pipeline, anti-rollback logic |
| Sourish | Cryptography / Scripting | Key generation, SHA-256 hashing, signing CLI, unit tests |
| Rishi | Edge Simulator / QA | Signing automation, edge agent mock install, README, docs |

---

## Repository Structure

```
Infoatact-Internship/
├── .github/
│   └── workflows/
│       └── sign-and-release.yml    <- Jagadesh (Week 2)
├── server/                          <- Jagadesh
│   └── app.py
├── crypto/                          <- Sourish
│   ├── generate_keys.py
│   ├── hash_firmware.py
│   └── sign_firmware.py
├── edge-agent/                      <- Rishi
│   ├── agent.py
│   ├── verify.py
│   └── mock_install.py
├── metadata/                        <- Harish
│   ├── sample_metadata.json
│   └── README.md
├── docs/                            <- Harish
│   ├── ARCHITECTURE.md
│   └── THREAT_MODEL.md
├── .gitignore                       <- Harish (Day 1)
└── README.md                        <- Rishi (Week 4)
```

---

## Weekly Integration Points

```
Week 1: Keys(Sourish) + Server(Jagadesh) + Signing(Rishi) + Structure(Harish)
Week 2: Pipeline(Jagadesh) + CLI(Sourish) + Bundle Upload(Rishi) + Security(Harish)
Week 3: Downloader(Jagadesh) + Verifier(Sourish) + Installer(Rishi) + State Machine(Harish)
Week 4: Rollback(Jagadesh) + Unit Tests(Sourish) + Docs(Rishi) + Integration Test(Harish)
        -> COMPLETE WORKING SYSTEM
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| CI/CD | GitHub Actions |
| Signing | Python `cryptography` library (RSA-2048 or ECDSA P-256) |
| Hashing | Python `hashlib` SHA-256 |
| Distribution Server | Flask or FastAPI |
| Edge Agent | Python 3.10+ |
| Key Storage (CI) | GitHub Secrets |
