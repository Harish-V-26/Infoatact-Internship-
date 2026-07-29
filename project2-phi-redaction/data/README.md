# Synthetic Clinical Notes Dataset

`sample_clinical_notes.json` contains 20 fully synthetic clinical notes used to test the PHI/PII redaction pipeline.

**Important:** All names, dates of birth, phone numbers, emails, and addresses in this file are fictional and were generated for testing purposes only. This dataset does **not** contain any real patient information (no real PHI).

## Format

```json
{
  "notes": [
    { "note_id": 1, "text": "..." },
    ...
  ]
}
```

Each note intentionally mixes:
- Patient names (should be redacted)
- Doctor names (should be redacted)
- Medical conditions named after people, e.g. Parkinson's disease, Alzheimer's disease, Crohn's disease, Huntington's disease, Tourette syndrome (should **not** be redacted — see issue #47)
- Phone numbers, emails, addresses, and dates of birth (should be redacted)

Use this file to validate both the regex baseline (#44) and the NLP detection layer (#46/#47/#48).
