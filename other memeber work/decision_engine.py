"""
decision_engine.py
Maps a numeric risk score to a CI/CD action decision.

Thresholds
──────────
  score >= 75  →  BLOCK   (critical risk — do not deploy)
  score >= 45  →  WARN    (significant risk — human review recommended)
  score >= 20  →  REVIEW  (low–moderate risk — flag for awareness)
  score <  20  →  ALLOW   (acceptable risk — proceed)
"""

from dataclasses import dataclass


@dataclass
class Decision:
    action: str          # BLOCK | WARN | REVIEW | ALLOW
    risk_score: float
    message: str
    emoji: str


_THRESHOLDS = [
    (75, "BLOCK",  "🔴 BLOCKED — Critical security risk detected. Deployment halted.",      "🔴"),
    (45, "WARN",   "🟠 WARNING — Significant issues found. Human review strongly advised.", "🟠"),
    (20, "REVIEW", "🟡 REVIEW  — Low–moderate risk. Flag for awareness.",                   "🟡"),
    (0,  "ALLOW",  "🟢 ALLOWED — No significant issues detected. Safe to proceed.",         "🟢"),
]


def make_decision(risk_score: float) -> Decision:
    """
    Returns a Decision dataclass based on the risk score.
    """
    for threshold, action, message, emoji in _THRESHOLDS:
        if risk_score >= threshold:
            return Decision(
                action=action,
                risk_score=risk_score,
                message=message,
                emoji=emoji,
            )
    # Fallback (should not reach here)
    return Decision("ALLOW", risk_score, "🟢 ALLOWED — No significant issues detected.", "🟢")