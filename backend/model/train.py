"""
train.py
One-time training script.

Usage
-----
    cd backend
    python model/train.py

Expects
-------
    backend/data/spam.csv  — CSV with at minimum two columns:
        • 'v1'  : label  ("ham" or "spam")
        • 'v2'  : message text

Output
------
    backend/model/spam_model.pkl  — serialised sklearn pipeline
"""

import os
import sys
import pandas as pd
import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ---------------------------------------------------------------------------
# Paths (relative to this script's location)
# ---------------------------------------------------------------------------
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_PATH   = os.path.join(SCRIPT_DIR, "..", "data", "spam.csv")
MODEL_PATH  = os.path.join(SCRIPT_DIR, "spam_model.pkl")


def load_dataset(path: str) -> pd.DataFrame:
    """Load and validate spam.csv."""
    if not os.path.exists(path):
        sys.exit(
            f"[train] ERROR: Dataset not found at '{path}'.\n"
            "Download the SMS Spam Collection dataset and save it as backend/data/spam.csv"
        )

    # The standard SMS Spam Collection has extra unnamed columns — keep only v1, v2
    df = pd.read_csv(path, encoding="latin-1")

    # Flexible column detection
    if {"v1", "v2"}.issubset(df.columns):
        df = df[["v1", "v2"]].rename(columns={"v1": "label", "v2": "text"})
    elif {"label", "text"}.issubset(df.columns):
        df = df[["label", "text"]]
    else:
        sys.exit(
            "[train] ERROR: spam.csv must have either ('v1','v2') or ('label','text') columns."
        )

    df.dropna(inplace=True)
    df["label"] = df["label"].str.strip().str.lower()

    print(f"[train] Dataset loaded: {len(df)} samples")
    print(df["label"].value_counts().to_string())
    return df


def build_pipeline() -> Pipeline:
    """Return an untrained TF-IDF + MultinomialNB sklearn Pipeline."""
    return Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    sublinear_tf=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    max_features=25_000,
                    min_df=2,
                ),
            ),
            (
                "clf",
                MultinomialNB(alpha=0.1),
            ),
        ]
    )


def train_and_evaluate(df: pd.DataFrame) -> Pipeline:
    """Split data, train pipeline, print metrics and return fitted model."""
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print(f"\n[train] Test accuracy: {acc * 100:.2f}%")
    print("\n[train] Classification report:")
    print(classification_report(y_test, y_pred))

    return pipeline


def save_model(pipeline: Pipeline, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(pipeline, path)
    print(f"[train] Model saved to '{path}'")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("[train] Starting model training …\n")
    df       = load_dataset(DATA_PATH)
    pipeline = train_and_evaluate(df)
    save_model(pipeline, MODEL_PATH)
    print("\n[train] Done! You can now start the Flask app with: python app.py")
