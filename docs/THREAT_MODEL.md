# Threat Model — Secure OTA Firmware Update System

**Owner:** Harish (Security & Integration Lead)
**Project:** Infotact Internship — Project 1: Logistics & IoT Edge
**Version:** 1.0 (Week 1)

---

## 1. System Overview

This system provides secure Over-The-Air (OTA) firmware updates for IoT edge devices
used in logistics and fleet tracking. The CI/CD pipeline signs firmware using asymmetric
cryptography, and the edge agent cryptographically verifies integrity before installation.

---

## 2. Assets to Protect

| Asset | Sensitivity | Impact if Compromised |
|-------|-------------|----------------------|
| Private signing key | CRITICAL | Attacker can sign and distribute any malicious firmware |
| Firmware binary | HIGH | Tampered binary = full fleet device takeover |
| Metadata / version info | MEDIUM | Manipulation enables rollback attacks |
| Distribution server | MEDIUM | Attacker could serve malicious bundles |
| GitHub Secrets store | HIGH | Key exfiltration if CI/CD is misconfigured |

---

## 3. Threat Actors

| Actor | Capability | Motivation |
|-------|-----------|------------|
| Supply chain attacker | Network interception, firmware injection | Fleet takeover, espionage |
| Insider threat | Access to CI/CD pipeline, key theft | Sabotage, financial gain |
| Nation-state actor | Advanced persistent threat, zero-days | Espionage, infrastructure disruption |
| Script kiddie | Public exploit tools | Opportunistic vandalism |

---

## 4. Attack Vectors & Mitigations

### Attack 1: Firmware Tampering (Man-in-the-Middle)
- **Description:** Attacker intercepts firmware in transit and modifies the binary
- **Impact:** Malicious code executes on all fleet devices simultaneously
- **Likelihood:** HIGH on unencrypted channels
- **Mitigation:**
  - SHA-256 hash verification detects any byte-level modification
  - RSA/ECDSA signature verification proves the firmware came from a trusted source
- **Implemented In:** Week 1 (hashing) + Week 3 (edge agent verification)

---

### Attack 2: Replay / Rollback Attack
- **Description:** Attacker replays a legitimately signed but older, vulnerable firmware
- **Impact:** Device runs known-vulnerable firmware, re-exploitable
- **Likelihood:** MEDIUM
- **Mitigation:**
  - Anti-rollback versioning: edge agent compares `incoming_version` vs `current_version`
  - Reject if `incoming_version < current_version`
- **Implemented In:** Week 4

---

### Attack 3: Private Key Compromise
- **Description:** Attacker steals the private signing key from CI/CD or developer machine
- **Impact:** Attacker gains full signing authority over any firmware
- **Likelihood:** LOW (with controls) / CRITICAL (if key is hardcoded or committed)
- **Mitigation:**
  - Key stored ONLY in GitHub Secrets — encrypted at rest, injected as env variable at runtime
  - `*.pem` files added to `.gitignore` on Day 1
  - Secret scanning enabled on repository
  - Key never appears in logs or build artifacts
- **Implemented In:** Week 1 (.gitignore) + Week 2 (GitHub Secrets)

---

### Attack 4: Rogue Update Server
- **Description:** DNS spoofing or BGP hijacking redirects devices to attacker's server
- **Impact:** Devices download attacker-controlled bundles
- **Likelihood:** MEDIUM
- **Mitigation:**
  - Public key is hardcoded inside the edge agent
  - Unsigned or wrongly-signed bundles are rejected even from a rogue server
- **Implemented In:** Week 3 (edge agent with embedded public key)

---

### Attack 5: CI/CD Pipeline Injection
- **Description:** Attacker modifies GitHub Actions workflow to exfiltrate the private key
- **Impact:** Full key compromise; malicious firmware shipped to all devices
- **Likelihood:** LOW (requires GitHub account compromise or bad PR merge)
- **Mitigation:**
  - Branch protection rules on `main` (require PR + review before merge)
  - Restrict who can push release tags
  - Regular audit of CI/CD logs
  - GitHub secret scanning + Dependabot alerts enabled
- **Implemented In:** Week 2

---

## 5. Trust Boundary Diagram

```
[Developer Workstation]
        |
        | (git push + release tag)
        v
[GitHub Repository] <──── GitHub Secrets (Private Key, never exposed in logs)
        |
        | (GitHub Actions triggered on tag)
        v
[CI/CD Runner] ──── Signs firmware ──── Produces metadata.json + .sig
        |
        | (Upload signed bundle)
        v
[Distribution Server] ──── Serves firmware.bin + metadata.json + .sig
        |
        | (HTTP download by edge agent)
        v
[IoT Edge Device] <──── Embedded Public Key (hardcoded, cannot be swapped)
        |
        | (Verify SHA-256 hash + RSA/ECDSA signature)
        v
   Pass -> Mock Install    OR    Fail -> CRITICAL Alert + Discard
```

---

## 6. Cryptographic Algorithm Choices

| Parameter | Choice | Justification |
|-----------|--------|---------------|
| Signing Algorithm | RSA-2048 or ECDSA P-256 | Industry standard; ECDSA preferred for smaller, faster signatures |
| Hash Function | SHA-256 | Collision-resistant, FIPS-approved, universally supported |
| Key Storage (CI) | GitHub Secrets | Encrypted at rest, injected only at runtime as environment variable |
| Key Storage (Device) | Embedded public key in agent | Public key only — safe and correct to embed |

---

## 7. Security Controls Summary

| Control | Type | Week |
|---------|------|------|
| `.gitignore` blocks `*.pem`, `*.key` | Preventive | Week 1 |
| SHA-256 hash verification on edge agent | Detective | Week 1–3 |
| RSA/ECDSA signature verification | Detective | Week 1–3 |
| GitHub Secrets for private key storage | Preventive | Week 2 |
| Branch protection on `main` | Preventive | Week 2 |
| Critical alert logging on verification failure | Detective | Week 3 |
| Anti-rollback version check | Preventive | Week 4 |

---

## 8. Out of Scope (v1.0)

- Hardware Security Modules (HSM) for key storage
- Certificate revocation (CRL / OCSP)
- Mutual TLS between edge device and distribution server
- Physical device tampering / hardware-level attacks
- Key rotation procedures

---

*Last Updated: Week 1 | Next Review: End of Week 4 after full integration test*
