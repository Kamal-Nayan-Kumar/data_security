"""
static_analyzer.py (FIXED & IMPROVED)

Scans source code for dangerous function calls and insecure patterns.

Improvements:
✔ Reverse shell detection
✔ Strong SQL injection detection
✔ Better subprocess detection
✔ Obfuscation patterns
✔ More real-world attack coverage
"""

DANGEROUS_PATTERNS = [

    # ─── Code execution ─────────────────────────────
    ("eval(",             "HIGH",   "Arbitrary code execution via eval()"),
    ("exec(",             "HIGH",   "Arbitrary code execution via exec()"),
    ("compile(",          "MEDIUM", "Dynamic code compilation detected"),

    # ─── OS / Shell injection ───────────────────────
    ("os.system(",        "HIGH",   "Shell injection risk via os.system()"),
    ("os.popen(",         "HIGH",   "Shell injection risk via os.popen()"),

    ("subprocess.call(",  "MEDIUM", "Potential shell injection via subprocess.call()"),
    ("subprocess.Popen(", "MEDIUM", "Potential shell injection via subprocess.Popen()"),
    ("subprocess.run(",   "MEDIUM", "Check shell=True usage in subprocess.run()"),

    ("shell=True",        "HIGH",   "Critical: shell=True enables command injection"),

    # ─── Deserialization ────────────────────────────
    ("pickle.loads(",     "HIGH",   "Unsafe deserialization via pickle.loads()"),
    ("pickle.load(",      "HIGH",   "Unsafe deserialization via pickle.load()"),
    ("yaml.load(",        "MEDIUM", "Use yaml.safe_load() instead of yaml.load()"),

    # ─── SQL Injection ──────────────────────────────
    ("SELECT",            "LOW",    "SQL query detected (review for injection)"),
    ("+ user_input",      "HIGH",   "SQL Injection risk via string concatenation"),
    ("WHERE",             "LOW",    "SQL WHERE clause detected"),

    ("% cursor.execute",  "MEDIUM", "Possible SQL injection via string formatting"),
    ("f\"SELECT",         "MEDIUM", "Possible SQL injection via f-string query"),
    ("f'SELECT",          "MEDIUM", "Possible SQL injection via f-string query"),

    # ─── Reverse shell patterns ─────────────────────
    ("socket.socket",     "HIGH",   "Socket usage — possible reverse shell"),
    ("dup2",              "HIGH",   "File descriptor duplication (reverse shell indicator)"),

    # ─── Obfuscation / encoded payloads ─────────────
    ("base64.b64decode",  "MEDIUM", "Encoded payload detected (possible obfuscation)"),

    # ─── Crypto issues ─────────────────────────────
    ("md5(",              "LOW",    "MD5 is cryptographically weak"),
    ("sha1(",             "LOW",    "SHA1 is cryptographically weak"),

    # ─── Dynamic behavior ──────────────────────────
    ("__import__(",       "HIGH",   "Dynamic import — potential code injection"),
]


def scan_static(code: str) -> list[dict]:
    """
    Returns a list of issue dicts:
    {
        severity,
        description,
        pattern,
        line,
        snippet
    }
    """

    issues = []
    lines = code.splitlines()

    # ─── Pattern-based detection ────────────────────
    for pattern, severity, description in DANGEROUS_PATTERNS:
        for line_num, line in enumerate(lines, start=1):
            if pattern in line:
                issues.append({
                    "severity": severity,
                    "description": description,
                    "pattern": pattern.strip(),
                    "line": line_num,
                    "snippet": line.strip()[:120],
                })
                break  # report once per file

    # ─── Advanced detections (NEW) ──────────────────

    #  Reverse shell detection (strong signal)
    if "socket.socket" in code and "dup2" in code:
        issues.append({
            "severity": "CRITICAL",
            "description": "Reverse shell pattern detected",
            "pattern": "socket + dup2",
            "line": "-",
            "snippet": "socket + dup2 combination"
        })

    #  SQL Injection detection (strong signal)
    if "SELECT" in code and "+ user_input" in code:
        issues.append({
            "severity": "HIGH",
            "description": "SQL Injection risk (user input concatenation)",
            "pattern": "SELECT + user_input",
            "line": "-",
            "snippet": "query concatenation"
        })

    #  Obfuscated execution
    if "base64" in code and "exec(" in code:
        issues.append({
            "severity": "HIGH",
            "description": "Obfuscated code execution via base64 + exec",
            "pattern": "base64 + exec",
            "line": "-",
            "snippet": "encoded payload execution"
        })

    return issues