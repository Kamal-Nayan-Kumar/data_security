"""
risk_engine.py (FINAL FIXED VERSION)

Fixes:
✔ Prevent score explosion (caps)
✔ Restore strong impact for HIGH / CRITICAL
✔ Add override rules for real threats
✔ Balanced AI + rule-based scoring
"""

SEVERITY_WEIGHTS = {
    "CRITICAL": 40,
    "HIGH":     25,
    "MEDIUM":   15,
    "LOW":       5,
}

# 🔥 Caps to prevent explosion
CATEGORY_CAPS = {
    "static": 50,
    "secret": 40,
    "dependency": 30,
    "config": 20,
    "ai": 30
}


def _issue_points(issues: list[dict], category: str) -> float:
    total = 0.0

    for issue in issues:
        sev = issue.get("severity", "LOW").upper()
        total += SEVERITY_WEIGHTS.get(sev, 5)

    return min(total, CATEGORY_CAPS[category])


def calculate_risk(
    static_issues: list[dict],
    secret_issues: list[dict],
    dep_issues: list[dict],
    config_issues: list[dict],
    ai_score: float,
) -> float:

    static_pts = _issue_points(static_issues, "static")
    secret_pts = _issue_points(secret_issues, "secret")
    dep_pts    = _issue_points(dep_issues, "dependency")
    config_pts = _issue_points(config_issues, "config")

    ai_pts = min(ai_score * 30, CATEGORY_CAPS["ai"])

    # 🔥 BASE SCORE (additive)
    risk = static_pts + secret_pts + dep_pts + config_pts + ai_pts

    # ─────────────────────────────────────────────
    # 🔥 OVERRIDE RULES (VERY IMPORTANT)
    # ─────────────────────────────────────────────

    # 🚨 CRITICAL issue → near block
    if any(i.get("severity") == "CRITICAL" for i in static_issues):
        return min(90 + ai_pts, 100)

    # 🚨 Multiple HIGH issues → strong boost
    high_count = sum(1 for i in static_issues if i.get("severity") == "HIGH")
    if high_count >= 2:
        risk += 25

    # 🚨 Secret + execution combo → very dangerous
    if static_pts > 30 and secret_pts > 20:
        risk += 20

    # 🚨 Reverse shell pattern boost
    if any("reverse shell" in i.get("description", "").lower() for i in static_issues):
        risk += 30

    return round(min(risk, 100.0), 2)


def risk_breakdown(
    static_issues: list[dict],
    secret_issues: list[dict],
    dep_issues: list[dict],
    config_issues: list[dict],
    ai_score: float,
) -> dict:

    static_pts = _issue_points(static_issues, "static")
    secret_pts = _issue_points(secret_issues, "secret")
    dep_pts    = _issue_points(dep_issues, "dependency")
    config_pts = _issue_points(config_issues, "config")
    ai_pts     = min(ai_score * 30, CATEGORY_CAPS["ai"])

    total = calculate_risk(
        static_issues,
        secret_issues,
        dep_issues,
        config_issues,
        ai_score
    )

    return {
        "static_points": static_pts,
        "secret_points": secret_pts,
        "dependency_points": dep_pts,
        "config_points": config_pts,
        "ai_points": ai_pts,
        "total": total,
    }