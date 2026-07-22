# Metadata Format — OTA Firmware Bundle

Each firmware release ships with a `metadata.json` file. The edge agent reads this
before downloading or installing anything.

## Schema

```json
{
  "version": "1.0.0",
  "hash": "<sha256-hex-of-firmware.bin>",
  "signature": "<base64-encoded-digital-signature>",
  "binary_url": "<url-to-download-firmware.bin>",
  "signed_at": "<ISO-8601-timestamp>",
  "algorithm": "RSA-2048-SHA256"
}
```

## Field Reference

| Field        | Type   | Description                                                         |
|--------------|--------|---------------------------------------------------------------------|
| `version`    | string | Semantic version (MAJOR.MINOR.PATCH) — used for anti-rollback check |
| `hash`       | string | SHA-256 hex digest of the raw `.bin` file                           |
| `signature`  | string | Base64-encoded RSA/ECDSA signature of the hash                      |
| `binary_url` | string | URL to download the firmware binary from                            |
| `signed_at`  | string | ISO 8601 UTC timestamp of when the signing occurred                 |
| `algorithm`  | string | Signing algorithm: `RSA-2048-SHA256` or `ECDSA-P256`               |

## Verification Rules (enforced by Edge Agent)

1. Download `metadata.json` first
2. Check `version >= current_installed_version` — reject if older (anti-rollback)
3. Download `firmware.bin` from `binary_url`
4. Compute SHA-256 of downloaded binary — must match `hash` field
5. Verify `signature` against `hash` using embedded public key — must pass
6. Only if both checks pass: proceed with mock install

> ⚠️ Failure at ANY step = discard entire bundle + log CRITICAL security alert
