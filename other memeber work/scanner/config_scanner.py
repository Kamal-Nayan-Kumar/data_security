"""
config_scanner.py
Scans config files (JSON, YAML, .env, .ini) for insecure settings.
"""

import json
import re

# Common weak / default passwords
WEAK_PASSWORDS = {"password", "1234", "12345", "123456", "admin", "root", "test", "qwerty", "pass", "secret"}


def _scan_json(content: str) -> list[dict]:
    issues = []
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return issues

    checks = [
        ("debug",           True,   "HIGH",   "Debug mode is enabled in config"),
        ("DEBUG",           True,   "HIGH",   "DEBUG mode is enabled in config"),
        ("ssl_verify",      False,  "HIGH",   "SSL verification is disabled"),
        ("verify_ssl",      False,  "HIGH",   "SSL verification is disabled"),
        ("allow_all_origins", True, "MEDIUM", "CORS allow_all_origins is enabled"),
        ("cors",            "*",    "MEDIUM", "CORS wildcard (*) is set"),
    ]

    for key, bad_value, severity, message in checks:
        if data.get(key) == bad_value:
            issues.append({"severity": severity, "description": message, "pattern": key, "line": None, "snippet": f'"{key}": {json.dumps(bad_value)}'})

    # Check password fields
    for key in ("password", "passwd", "db_password", "admin_password"):
        val = data.get(key, "")
        if isinstance(val, str) and val.lower() in WEAK_PASSWORDS:
            issues.append({"severity": "HIGH", "description": f"Weak password in config key '{key}'", "pattern": key, "line": None, "snippet": f'"{key}": "****"'})

    return issues


def _scan_env(content: str) -> list[dict]:
    issues = []
    for line_num, line in enumerate(content.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # DEBUG=true / DEBUG=1
        if re.match(r'(?i)DEBUG\s*=\s*(true|1|yes)', line):
            issues.append({"severity": "HIGH", "description": "DEBUG mode enabled in .env", "pattern": "DEBUG", "line": line_num, "snippet": line})

        # Plaintext secrets
        if re.match(r'(?i)(SECRET_KEY|APP_SECRET|JWT_SECRET)\s*=\s*.{1,20}$', line):
            issues.append({"severity": "HIGH", "description": "Very short or possible weak secret key in .env", "pattern": "SECRET_KEY", "line": line_num, "snippet": re.sub(r'=.*', '=****', line)})

        # SSL disabled
        if re.match(r'(?i)SSL_VERIFY\s*=\s*(false|0|no)', line):
            issues.append({"severity": "HIGH", "description": "SSL verification disabled in .env", "pattern": "SSL_VERIFY", "line": line_num, "snippet": line})

    return issues


def _scan_yaml_text(content: str) -> list[dict]:
    """Lightweight text-based YAML scan (no pyyaml required)."""
    issues = []
    for line_num, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()

        if re.match(r'(?i)debug\s*:\s*(true|yes|1)', stripped):
            issues.append({"severity": "HIGH", "description": "Debug mode enabled in YAML config", "pattern": "debug", "line": line_num, "snippet": stripped})

        if re.match(r'(?i)allow_all_origins\s*:\s*(true|yes|1)', stripped):
            issues.append({"severity": "MEDIUM", "description": "CORS allow_all_origins enabled in YAML", "pattern": "allow_all_origins", "line": line_num, "snippet": stripped})

        if re.match(r'(?i)(password|passwd)\s*:\s*\S+', stripped):
            val_match = re.search(r':\s*(.+)', stripped)
            if val_match:
                val = val_match.group(1).strip().strip('"\'')
                if val.lower() in WEAK_PASSWORDS:
                    issues.append({"severity": "HIGH", "description": "Weak password in YAML config", "pattern": "password", "line": line_num, "snippet": re.sub(r':\s*.+', ': ****', stripped)})

    return issues


def scan_config(file_path: str, content: str) -> list[dict]:
    """
    Dispatch to the right sub-scanner based on file extension.
    Returns list of issue dicts.
    """
    fname = file_path.replace("\\", "/").lower()

    if fname.endswith(".json"):
        return _scan_json(content)
    elif fname.endswith(".env") or "/.env." in fname or fname.endswith("/.env"):
        return _scan_env(content)
    elif fname.endswith(".yaml") or fname.endswith(".yml"):
        return _scan_yaml_text(content)
    elif fname.endswith(".ini") or fname.endswith(".cfg"):
        # Basic INI scan
        issues = []
        for line_num, line in enumerate(content.splitlines(), start=1):
            if re.match(r'(?i)debug\s*=\s*(true|1|yes)', line.strip()):
                issues.append({"severity": "HIGH", "description": "Debug mode in INI config", "pattern": "debug", "line": line_num, "snippet": line.strip()})
        return issues

    return []