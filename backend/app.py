"""
app.py
Flask entry point for the Spam Email Detector API.

Endpoints
---------
POST /predict   { "text": "..." }            → unified prediction response
POST /upload    multipart/form-data file=…   → parse file then predict

Run
---
    cd backend
    python app.py
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import traceback

from utils.predictor   import load_model, predict
from utils.explainer   import explain, build_reasons
from utils.email_parser import parse_file

app = Flask(__name__)
CORS(app)   # allow requests from the local HTML frontend

# ---------------------------------------------------------------------------
# Startup — load model once
# ---------------------------------------------------------------------------
try:
    load_model()
except FileNotFoundError as exc:
    print(f"[app] WARNING: {exc}")
    print("[app] The server will start but /predict and /upload will return 503 until the model is trained.")


# ---------------------------------------------------------------------------
# Helper: build the unified response dict
# ---------------------------------------------------------------------------
def _build_response(text: str) -> dict:
    """Run prediction + explanation on *text* and return the response dict."""
    # 1. Predict
    pred_result  = predict(text)
    label        = pred_result["label"]
    confidence   = pred_result["confidence"]

    # 2. Explain
    explanation  = explain(text)
    reasons      = build_reasons(explanation)

    # 3. Highlighting is handled client-side using the explanation payload
    #    We send the raw explanation so the JS highlighter can do rich DOM work.
    return {
        "prediction":   label,
        "confidence":   confidence,
        "reasons":      reasons,
        "explanation":  explanation,   # { spam_keywords, urgency_phrases, suspicious_links }
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route("/predict", methods=["POST"])
def predict_route():
    """Accept JSON { "text": "..." } and return the prediction."""
    try:
        data = request.get_json(force=True, silent=True)

        if not data or "text" not in data:
            return jsonify({"error": "Request body must contain a 'text' field."}), 400

        text = data["text"].strip()

        if not text:
            return jsonify({"error": "Input text cannot be empty."}), 400

        return jsonify(_build_response(text)), 200

    except RuntimeError as exc:
        # Model not loaded
        return jsonify({"error": str(exc)}), 503

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Internal server error."}), 500


@app.route("/upload", methods=["POST"])
def upload_route():
    """Accept a multipart file (.txt or .eml) and return the prediction."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part in the request. Use key 'file'."}), 400

        uploaded = request.files["file"]

        if uploaded.filename == "":
            return jsonify({"error": "No file selected."}), 400

        file_bytes = uploaded.read()
        text       = parse_file(uploaded.filename, file_bytes)

        if not text.strip():
            return jsonify({"error": "The uploaded file appears to be empty."}), 400

        return jsonify(_build_response(text)), 200

    except ValueError as exc:
        # Unsupported file type or parse error
        return jsonify({"error": str(exc)}), 400

    except RuntimeError as exc:
        # Model not loaded
        return jsonify({"error": str(exc)}), 503

    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Internal server error."}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
