"""
secret_scanner.py
Detects hardcoded secrets, API keys, passwords, and tokens in source files.
"""

import re

# Each tuple: (label, regex_pattern, severity)
SECRET_PATTERNS = [
    # AWS
    ("AWS Access Key",        r'AKIA[0-9A-Z]{16}',                                  "CRITICAL"),
    ("AWS Secret Key",        r'(?i)aws_secret[_-]?access[_-]?key\s*=\s*["\']?\S+', "CRITICAL"),

    # Generic API keys
    ("API Key Assignment",    r'(?i)api[_-]?key\s*=\s*["\'][A-Za-z0-9_\-]{8,}["\']', "HIGH"),
    ("API Token",             r'(?i)api[_-]?token\s*=\s*["\'][A-Za-z0-9_\-]{8,}["\']', "HIGH"),

    # Passwords
    ("Hardcoded Password",    r'(?i)password\s*=\s*["\'][^"\']{4,}["\']',           "HIGH"),
    ("Hardcoded Passwd",      r'(?i)passwd\s*=\s*["\'][^"\']{4,}["\']',             "HIGH"),

    # Tokens / secrets
    ("Auth Token",            r'(?i)(auth|access)[_-]?token\s*=\s*["\'][A-Za-z0-9._\-]{10,}["\']', "HIGH"),
    ("Secret Key",            r'(?i)secret[_-]?key\s*=\s*["\'][^"\']{6,}["\']',    "HIGH"),
    ("Private Key Header",    r'-----BEGIN (RSA |EC )?PRIVATE KEY-----',             "CRITICAL"),

    # Database
    ("DB Password",           r'(?i)db[_-]?pass(word)?\s*=\s*["\'][^"\']{4,}["\']', "HIGH"),
    ("Connection String",     r'(?i)(mongodb|mysql|postgres|redis):\/\/\S+:\S+@',   "HIGH"),

    # GitHub / GitLab
    ("GitHub Token",          r'ghp_[A-Za-z0-9]{36}',                               "CRITICAL"),
    ("GitLab Token",          r'glpat-[A-Za-z0-9\-]{20}',                           "CRITICAL"),

    # Slack
    ("Slack Token",           r'xox[baprs]-[0-9A-Za-z\-]{10,}',                     "CRITICAL"),

    # Generic long random strings that look like secrets
    ("Possible Secret",       r'(?i)(secret|token|key)\s*=\s*["\'][A-Za-z0-9+/]{32,}["\']', "MEDIUM"),
]


def scan_secrets(code: str) -> list[dict]:
    """
    Returns list of issue dicts for any detected secrets.
    """
    issues = []
    lines = code.splitlines()

    for label, pattern, severity in SECRET_PATTERNS:
        for line_num, line in enumerate(lines, start=1):
            if re.search(pattern, line):
                # Mask the actual secret value in the snippet
                masked = re.sub(r'(["\'])[A-Za-z0-9+/=_\-]{6,}(["\'])', r'\1****\2', line.strip())
                issues.append({
                    "severity": severity,
                    "description": f"{label} detected",
                    "pattern": label,
                    "line": line_num,
                    "snippet": masked[:120],
                })
                break  # One report per pattern per file

    return issues