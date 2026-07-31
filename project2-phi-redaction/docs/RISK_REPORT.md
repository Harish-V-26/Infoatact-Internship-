# Re-Identification Risk Report & HIPAA Safe Harbor Alignment

**Project 2 — PHI/PII Redaction Pipeline for LLMs**
**Author:** Harish | **Status:** Current as of pipeline state on this date — will need a follow-up pass once #48, #50-53, #61-63 are closed.

---

## 1. Purpose

This report evaluates how the current redaction pipeline (`project2-phi-redaction/proxy/app/services/redaction.py`) aligns with the HIPAA Safe Harbor method, which requires removal of 18 categories of identifiers before health information is considered de-identified. It is based on an actual test run against all 20 notes in `data/sample_clinical_notes.json`, not a theoretical review.

## 2. HIPAA Safe Harbor — 18 Identifiers, Current Coverage

| # | Identifier | Status | Notes |
|---|---|---|---|
| 1 | Names | ✅ Handled | spaCy PERSON detection, with medical eponym protection (Parkinson's, Crohn's, etc. correctly excluded) |
| 2 | Geographic subdivisions smaller than a state | ❌ Not handled | No address/location detection exists yet — issue #48, open |
| 3 | Dates (except year) — DOB, admission, discharge | ❌ Not handled | Confirmed leaking in 13/20 test notes — issue #44, open |
| 4 | Phone numbers | ⚠️ Partial | Standard format handled; `(555) 123-4567` format leaks — confirmed in 4/20 notes, issue #61, open |
| 5 | Fax numbers | ❌ Not applicable to current dataset | No test coverage yet |
| 6 | Email addresses | ✅ Handled | Verified clean across all 20 test notes |
| 7 | Social Security numbers | ❌ Not handled | No SSNs in current test dataset, no detection logic either |
| 8 | Medical record numbers | ❌ Not handled | Not yet in scope |
| 9 | Health plan beneficiary numbers | ❌ Not handled | Not yet in scope |
| 10 | Account numbers | ❌ Not handled | Not yet in scope |
| 11 | Certificate/license numbers | ❌ Not handled | Not yet in scope |
| 12 | Vehicle identifiers | ❌ Not applicable | Not relevant to clinical notes use case |
| 13 | Device identifiers | ❌ Not applicable | Not relevant to clinical notes use case |
| 14 | URLs | ❌ Not handled | Not yet in scope |
| 15 | IP addresses | ❌ Not handled | Not yet in scope |
| 16 | Biometric identifiers | ❌ Not applicable | Not relevant to text-based notes |
| 17 | Full-face photos | ❌ Not applicable | Text-only pipeline |
| 18 | Any other unique identifying number/code | ❌ Not handled | Not yet in scope |

**Bottom line: the pipeline currently satisfies roughly 1.5 of 18 Safe Harbor categories** (names, partial phone). It is **not yet compliant** and should not be treated as production-ready for real PHI until at minimum #44 (dates), #61 (phone fix), and #48 (addresses) are closed.

## 3. Known Bugs (verified by direct test run, not just code review)

| Bug | Evidence | Tracking issue |
|---|---|---|
| Phone regex misses `(555) 123-4567` format | Leaked in notes #1, #5, #10, #16 | #61 |
| spaCy misclassifies place names as PERSON, over-redacting | "Lakeview" (#6) and "Chestnut Drive" (#12) wrongly replaced with `[PATIENT_NAME]` | #62 |
| No date masking at all | 13/20 notes leak DOB or visit dates | #44 |
| No address/location detection | 0/18 identifier categories 2 handled | #48 |
| No tokenization — redaction is destructive, not reversible | Vault doesn't exist yet | #50 |

## 4. Residual Re-Identification Risk (current state)

Given the gaps above, a motivated party could still re-identify a patient from a "redacted" note today via:
- **Direct dates** — a DOB combined with even a partial name fragment or condition is often enough to re-identify someone in a small population (a known weakness of Safe Harbor when dates aren't removed).
- **Addresses** — hospital/clinic addresses combined with a rough timeframe narrow down patient identity significantly, especially in smaller towns.
- **Phone number leakage** — a leaked phone number is close to directly identifying, since it maps to one household.

**Risk level: High, in current state.** This should be explicitly communicated to the team and not understated in review — the pipeline demonstrates a viable *architecture* (regex + NLP + planned tokenization vault) but is not yet functionally de-identifying data reliably.

## 5. What Closes the Gap

Once the following issues are closed and re-verified against `data/sample_clinical_notes.json`, coverage should jump substantially:

- #44 (Jagadesh) — date masking
- #61 (Rishi) — phone regex fix
- #62 (Rishi) — false-positive fix
- #48 (Rishi) — address/location detection
- #50, #51, #52 (Sourish) — tokenization vault, making redaction reversible rather than destructive, and enabling the LLM response to be restored with real values for the clinical user

## 6. Verification Method

All findings in this report came from actually running `process_text()` from `app/services/redaction.py` against the real 20-note synthetic dataset and checking outputs programmatically for leaked phone numbers, emails, and dates, plus manually diffing for over-redaction. Raw before/after pairs for all 20 notes are preserved for the team's review (not committed to the repo, since even synthetic PHI-shaped data shouldn't accumulate in version control unnecessarily — available on request).

## 7. Recommendation on #57 (Final Integration Test)

**#57 should stay open.** Running a "final" integration test before #44, #48, #50-52, #61, #62 are closed would not be a meaningful final test — it would just re-confirm the same gaps documented here. Recommend #57 be picked up only after those are done, at which point it should re-run this same verification method and confirm 0 leaks across all 18 applicable identifier categories.
