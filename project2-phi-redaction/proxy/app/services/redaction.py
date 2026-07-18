"""
Pre-processing / de-identification layer.

This runs BEFORE any text leaves the proxy toward the external LLM.

TODO (Jagadesh - issue #44): implement regex-based de-identification.
Must detect and mask, at minimum:
  - phone numbers (e.g. 555-123-4567, (555) 123-4567)
  - emails
  - standard date formats (DOB, visit dates - e.g. 1985-03-14, 03/14/1985)

Replace matches with placeholders such as "[PHONE]", "[EMAIL]", "[DATE]"
so the LLM still has structural context without the actual identifier.
Names and addresses are intentionally NOT handled here - that is the
NLP layer's job (issue #46, Sourish/Rishi).

IMPORTANT - logging discipline: never log the raw or redacted note text
at INFO level or above. Only log metadata (length, request_id, counts of
matches found). Logging real note content, even redacted, risks leaking
PHI into log files that aren't access-controlled the same way the data
store is.
"""

import logging

logger = logging.getLogger(__name__)


def process_text(raw_text: str) -> str:
    logger.info("process_text called length=%d", len(raw_text))

    # Placeholder passthrough - Jagadesh, replace the line below with the
    # actual regex de-identification pipeline (issue #44).
    cleaned_text = raw_text

    return cleaned_text
