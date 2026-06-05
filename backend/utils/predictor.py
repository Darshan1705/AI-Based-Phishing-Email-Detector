"""
predictor.py
Loads the trained TF-IDF + Naive Bayes pipeline from disk and
exposes predict() for inference.
"""

import os
import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "model", "spam_model.pkl")

_model = None  # module-level singleton


def load_model():
    """Load the pickled pipeline into memory. Called once at app startup."""
    global _model
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model file not found at '{MODEL_PATH}'. "
            "Please run 'python model/train.py' first."
        )
    _model = joblib.load(MODEL_PATH)
    print(f"[predictor] Model loaded from {MODEL_PATH}")


def predict(text: str) -> dict:
    """
    Run inference on the provided text.

    Returns
    -------
    dict
        {
            "label":      "spam" | "not spam",
            "confidence": float  (0–100, percentage of the winning class)
        }
    """
    if _model is None:
        raise RuntimeError("Model not loaded. Call load_model() first.")

    proba = _model.predict_proba([text])[0]          # shape: (2,)
    classes = list(_model.classes_)                  # e.g. ["ham", "spam"]

    spam_idx = classes.index("spam")
    spam_prob = proba[spam_idx] * 100

    label = "spam" if spam_prob >= 50 else "not spam"
    confidence = spam_prob if label == "spam" else (100 - spam_prob)

    return {
        "label": label,
        "confidence": round(confidence, 2),
    }
