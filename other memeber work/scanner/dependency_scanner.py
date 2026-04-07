"""
dependency_scanner.py
Scans requirements.txt and package.json for known vulnerable or outdated packages.
"""

import json
import re

# Python packages with known vulnerable version patterns
PYTHON_VULNERABLE = [
    ("flask",        r"flask\s*==\s*0\.",         "Flask 0.x is outdated — upgrade to 2.x+"),
    ("django",       r"django\s*[<]=?\s*[12]\.",  "Django version is outdated, use 4.x+"),
    ("requests",     r"requests\s*==\s*2\.[0-9]\.", "Requests 2.0–2.9 has known vulnerabilities"),
    ("pyyaml",       r"pyyaml\s*[<]=?\s*5\.",     "PyYAML < 5.4 is vulnerable to arbitrary code execution"),
    ("pillow",       r"pillow\s*[<]=?\s*8\.",      "Pillow < 8.x has multiple CVEs"),
    ("cryptography", r"cryptography\s*[<]=?\s*3\.", "Old cryptography library — upgrade to 39+"),
    ("urllib3",      r"urllib3\s*[<]=?\s*1\.",     "urllib3 < 2.x has known vulnerabilities"),
    ("jinja2",       r"jinja2\s*[<]=?\s*2\.",      "Jinja2 2.x has template injection risks"),
    ("paramiko",     r"paramiko\s*[<]=?\s*2\.",    "Old Paramiko — upgrade to 3.x"),
    ("sqlalchemy",   r"sqlalchemy\s*[<]=?\s*1\.",  "SQLAlchemy 1.x is outdated"),
]

# npm packages flagged for review
NPM_FLAGGED = [
    ("lodash",      "lodash has had prototype pollution CVEs — ensure version >= 4.17.21"),
    ("axios",       "axios < 0.21.2 is vulnerable to SSRF — verify version"),
    ("minimist",    "minimist < 1.2.6 is vulnerable to prototype pollution"),
    ("node-fetch",  "node-fetch < 2.6.7 has known vulnerabilities"),
    ("express",     "Verify Express version — old versions have DoS vulnerabilities"),
    ("moment",      "moment.js is deprecated — consider date-fns or dayjs"),
    ("serialize-javascript", "serialize-javascript < 3.1.0 has XSS vulnerability"),
    ("tar",         "tar < 6.1.9 has arbitrary file write CVE"),
    ("shelljs",     "shelljs may enable shell injection if inputs are unsanitized"),
    ("jsonwebtoken","Verify jsonwebtoken version — old versions allow algorithm confusion"),
]


def scan_dependencies(file_path: str, content: str) -> list[dict]:
    """
    Returns a list of dependency issue dicts.
    """
    issues = []
    fname = file_path.replace("\\", "/")

    # ---- Python: requirements.txt ----
    if fname.endswith("requirements.txt"):
        for pkg_name, pattern, message in PYTHON_VULNERABLE:
            for line_num, line in enumerate(content.splitlines(), start=1):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        "severity": "MEDIUM",
                        "description": message,
                        "pattern": pkg_name,
                        "line": line_num,
                        "snippet": line.strip(),
                    })
                    break

    # ---- JavaScript: package.json ----
    elif fname.endswith("package.json"):
        try:
            data = json.loads(content)
            all_deps = {}
            all_deps.update(data.get("dependencies", {}))
            all_deps.update(data.get("devDependencies", {}))

            for pkg_name, message in NPM_FLAGGED:
                if pkg_name in all_deps:
                    issues.append({
                        "severity": "MEDIUM",
                        "description": message,
                        "pattern": pkg_name,
                        "line": None,
                        "snippet": f'"{pkg_name}": "{all_deps[pkg_name]}"',
                    })
        except json.JSONDecodeError:
            issues.append({
                "severity": "LOW",
                "description": "package.json is malformed — could not parse",
                "pattern": "JSON parse error",
                "line": None,
                "snippet": "",
            })

    return issues