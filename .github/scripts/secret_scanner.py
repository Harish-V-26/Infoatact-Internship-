import os
import re
import sys

DANGER_PATTERNS = [
    (r"-----BEGIN RSA PRIVATE KEY-----", "RSA Private Key"),
    (r"-----BEGIN EC PRIVATE KEY-----", "EC Private Key"),
    (r"-----BEGIN PRIVATE KEY-----", "PKCS8 Private Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
    (r"password\s*=\s*['\"][^'\"]{6,}['\"]", "Hardcoded Password"),
    (r"api_key\s*=\s*['\"][^'\"]{6,}['\"]", "Hardcoded API Key"),
]

SCAN_EXTENSIONS = [".py", ".yml", ".yaml", ".json", ".env", ".sh"]

SKIP_PATHS = [
    ".git", "__pycache__",
    "docs/signing_history.json",
    ".github/scripts/secret_scanner.py",
]


def should_skip(filepath):
    return any(skip in filepath for skip in SKIP_PATHS)


def scan_file(filepath):
    findings = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                for pattern, label in DANGER_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append({
                            "file": filepath,
                            "line": line_num,
                            "type": label
                        })
    except Exception:
        pass
    return findings


def main():
    print("[*] Starting secret scan...")
    all_findings = []

    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if ".git" not in d]
        for filename in files:
            filepath = os.path.join(root, filename)
            if should_skip(filepath):
                continue
            if os.path.splitext(filename)[1] not in SCAN_EXTENSIONS:
                continue
            all_findings.extend(scan_file(filepath))

    if all_findings:
        print("\n[CRITICAL] SECRETS DETECTED - PIPELINE BLOCKED")
        for f in all_findings:
            print(f"  File: {f['file']}:{f['line']} - {f['type']}")
        print("\nACTION: Remove secrets and use GitHub Secrets instead.")
        sys.exit(1)
    else:
        print("[OK] No secrets detected. Safe to proceed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
