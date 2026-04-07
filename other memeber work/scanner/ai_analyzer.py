"""
ai_analyzer.py (FIXED & IMPROVED)

Full pipeline:
Code → CodeBERT → PCA → Classifier → Calibrated AI score

Fixes:
✔ Reduced false positives
✔ AI calibration
✔ Stronger heuristics
✔ Safe fallback handling
"""

import re
import os
import pickle as pkl

# ─── Globals ─────────────────────────────────────────────
_tokenizer = None
_codebert_model = None
_codebert_available = False

_classifier = None
_classifier_loaded = False

_pca = None
_pca_loaded = False

CLASSIFIER_PATH = os.path.join(os.path.dirname(__file__), "..", "classifier.pkl")
PCA_PATH = os.path.join(os.path.dirname(__file__), "..", "pca.pkl")

# ─── Loaders ─────────────────────────────────────────────

def _load_codebert():
    global _tokenizer, _codebert_model, _codebert_available

    if _tokenizer is not None:
        return _codebert_available

    try:
        from transformers import AutoTokenizer, AutoModel
        import torch

        _tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        _codebert_model = AutoModel.from_pretrained("microsoft/codebert-base")
        _codebert_model.eval()

        _codebert_available = True
        print("[AI] CodeBERT loaded successfully.")
    except Exception as e:
        print(f"[AI] CodeBERT failed: {e}")
        _codebert_available = False

    return _codebert_available


def _load_classifier():
    global _classifier, _classifier_loaded

    if _classifier_loaded:
        return _classifier is not None

    _classifier_loaded = True

    if not os.path.exists(CLASSIFIER_PATH):
        print("[AI] No classifier found.")
        return False

    try:
        with open(CLASSIFIER_PATH, "rb") as f:
            _classifier = pkl.load(f)

        print("[AI] Trained classifier loaded successfully.")
        return True
    except Exception as e:
        print(f"[AI] Classifier load failed: {e}")
        return False


def _load_pca():
    global _pca, _pca_loaded

    if _pca_loaded:
        return _pca is not None

    _pca_loaded = True

    if not os.path.exists(PCA_PATH):
        print("[AI] No PCA found.")
        return False

    try:
        with open(PCA_PATH, "rb") as f:
            _pca = pkl.load(f)

        print("[AI] PCA loaded successfully.")
        return True
    except Exception as e:
        print(f"[AI] PCA load failed: {e}")
        return False


# ─── Heuristic signals ───────────────────────────────────

HEURISTIC_SIGNALS = [
    (r'\beval\s*\(', 0.55, True),
    (r'\bexec\s*\(', 0.55, True),
    (r'os\.system\s*\(', 0.45, True),
    (r'os\.popen\s*\(', 0.45, True),
    (r'pickle\.loads?\s*\(', 0.50, True),
    (r'__import__\s*\(', 0.45, True),
    (r'subprocess\.(call|Popen|run)\s*\(', 0.30, True),
    (r'base64\.b64decode', 0.20, True),

    # 🔥 NEW (important improvements)
    (r'SELECT\s+.*\+\s*\w+', 0.5, True),       # SQLi
    (r'WHERE\s+.*\+\s*\w+', 0.5, True),
    (r'socket\.socket.*dup2', 0.6, True),     # reverse shell

    (r'AKIA[0-9A-Z]{16}', 0.70, True),
    (r'-----BEGIN.*PRIVATE KEY', 0.70, True),
]


def _heuristic_score(code: str) -> float:
    score = 0.0

    for pattern, weight, is_regex in HEURISTIC_SIGNALS:
        if re.search(pattern, code) if is_regex else (pattern in code):
            score += weight

    return min(score, 1.0)


# ─── Embedding ───────────────────────────────────────────

def get_embedding(code: str):
    if not _load_codebert():
        return None

    import torch

    inputs = _tokenizer(
        code,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True
    )

    with torch.no_grad():
        outputs = _codebert_model(**inputs)

    return outputs.last_hidden_state.mean(dim=1).numpy()


# ─── MAIN AI FUNCTION ───────────────────────────────────

def ai_risk_score(code: str) -> float:

    heuristic = _heuristic_score(code)

    # ── FULL AI PATH ──
    if _load_classifier() and _load_codebert() and _load_pca():
        embedding = get_embedding(code)

        if embedding is not None:
            try:
                embedding = _pca.transform(embedding)

                prob = float(_classifier.predict_proba(embedding)[0][1])

                # 🔥 CALIBRATION FIX
                if prob > 0.85:
                    score = prob
                elif prob > 0.65:
                    score = prob * 0.6
                elif prob > 0.5:
                    score = prob * 0.3
                else:
                    score = prob * 0.1

                # 🔥 SAFE OVERRIDE
                if heuristic < 0.2 and prob < 0.7:
                    score *= 0.2

                return min(score, 1.0)

            except Exception as e:
                print("[AI] Prediction failed:", e)

    # ── FALLBACK ──
    if _load_codebert():
        embedding = get_embedding(code)

        if embedding is not None:
            norm = float((embedding ** 2).sum() ** 0.5)
            return min(heuristic + min(norm / 150.0, 0.2) * 0.1, 1.0)

    return heuristic


# ─── DEBUG INFO ─────────────────────────────────────────

def get_ai_details(code: str) -> dict:
    heuristic = _heuristic_score(code)
    score = ai_risk_score(code)

    return {
        "ai_score": round(score, 3),
        "heuristic_score": round(heuristic, 3),
        "mode": (
            "full_ai"
            if _classifier is not None
            else "fallback"
        )
    }