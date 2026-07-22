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
IDLE -> POLLING -> DOWNLOADING -> VERIFYING -> APPLYING -> IDLE
                                       |
                                       v (on failure)
                                    FAULT + ALERT LOG
```

### State Definitions and Valid Transitions

| State | Meaning | Valid Next States | Triggered By |
|-------|---------|-------------------|---------------|
| **IDLE** | Agent is idle, no active update cycle | POLLING | Timer tick / manual trigger |
| **POLLING** | Checking server `/manifest.json` for a newer version | DOWNLOADING, IDLE | Manifest fetch result |
| **DOWNLOADING** | Fetching firmware in chunks from server | VERIFYING, FAULT | Download completes / fails |
| **VERIFYING** | Checking SHA-256 hash + digital signature | APPLYING, FAULT | Hash/signature match or mismatch |
| **APPLYING** | Installing verified firmware, updating version | IDLE | Install completes |
| **FAULT** | A check failed — payload discarded, incident logged | IDLE | Recovery / next poll cycle |

### Rule
> The agent **never** transitions from VERIFYING to APPLYING unless **both** the SHA-256 hash check **and** the digital signature check pass. A failure at either layer routes to FAULT, never partially applies an update.

---

## Logging Framework

Every state transition prints a structured console line:
```
[STATE TRANSITION] <FROM> --> <TO>
```

Every **failure** (any transition into `FAULT`) additionally writes a JSON incident report via `edge-agent/incident_logger.py` to `edge-agent/logs/INC-<timestamp>.json`:

```json
{
  "incident_id": "INC-20260629061000",
  "timestamp": "2026-06-29T06:10:00Z",
  "state_at_failure": "VERIFYING",
  "firmware_version": "1.0.0",
  "failure_reason": "SHA-256 mismatch - download corrupted or tampered",
  "action_taken": "Payload discarded - rollback to current version",
  "alert_level": "CRITICAL"
}
```

| Field | Purpose |
|-------|---------|
| `incident_id` | Unique, timestamp-based, used as the log filename |
| `state_at_failure` | Which state the agent was in when it failed |
| `failure_reason` | Human-readable cause (hash mismatch, signature invalid, server unreachable, etc.) |
| `action_taken` | What the agent did in response — always fail-safe (discard, never partially install) |
| `alert_level` | `INFO` (e.g. server unreachable), `WARNING` (e.g. download failed), or `CRITICAL` (e.g. tampering detected) |

This gives auditors a timestamped, file-based trail of every security-relevant event without needing to parse console output.

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
│       ├── sign-and-release.yml    <- Harish (3-job CI/CD pipeline)
│       └── secret-scan.yml         <- Harish
├── server/                          <- Jagadesh
│   ├── app.py
│   ├── auth.py
│   ├── rate_limiter.py
│   ├── logger.py
│   ├── manifest.py
│   └── version_registry.py
├── crypto/                          <- Sourish
│   ├── rsa_keygen.py
│   ├── ecdsa_keygen.py
│   ├── sha256_hash.py
│   ├── engine.py
│   ├── fingerprint.py
│   └── sig_bundle.py
├── edge-agent/                      <- Rishi
│   ├── agent.py
│   ├── incident_logger.py
│   ├── sign_helper.py
│   └── create_dummy_firmware.py
├── metadata/                        <- Harish
│   ├── sample_metadata.json
│   └── README.md
├── docs/                            <- Harish
│   ├── ARCHITECTURE.md
│   └── THREAT_MODEL.md
├── tests/                           <- Harish
│   ├── integration_test.py
│   ├── malicious_actor_test.py
│   └── end_to_end_demo.py
├── .gitignore                       <- Harish (Day 1)
└── README.md
```

---

## Weekly Integration Points

```
Week 1: Keys(Sourish) + Server(Jagadesh) + Signing(Rishi) + Structure(Harish)
Week 2: Pipeline(Harish) + Crypto Engine(Sourish) + Secure Server(Jagadesh) + State Machine(Rishi)
Week 3: Live Manifest(Jagadesh) + Real Verification(Rishi+Sourish) + Tamper Tests(Harish)
Week 4: Rollback(Jagadesh) + Unit Tests(Sourish) + Docs(Rishi) + Final Integration Test(Harish)
        -> COMPLETE WORKING SYSTEM
```

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| CI/CD | GitHub Actions |
| Signing | Python `cryptography` library (RSA-2048 PSS or ECDSA P-256) |
| Hashing | Python `hashlib` SHA-256 |
| Distribution Server | Flask |
| Edge Agent | Python 3.11+ |
| Key Storage (CI) | GitHub Secrets |
