# SpamShield — AI-Based Spam Email Detector

A full-stack web application that uses **TF-IDF + Multinomial Naive Bayes** to classify emails as spam or not spam, with confidence scoring, three-tier keyword highlighting, and file upload support.

---

## Project Structure

```
6th sem-mini project/
├── backend/
│   ├── app.py                  ← Flask API server
│   ├── requirements.txt
│   ├── data/
│   │   └── spam.csv            ← ⚠ You must provide this (see below)
│   ├── model/
│   │   ├── train.py            ← Run once to train the model
│   │   └── spam_model.pkl      ← Auto-generated after training
│   └── utils/
│       ├── predictor.py
│       ├── explainer.py
│       └── email_parser.py
└── frontend/
    ├── index.html
    ├── css/style.css
    └── js/
        ├── main.js
        ├── highlighter.js
        └── uploader.js
```

---

## Step-by-Step Setup

### 1. Get the Dataset

Download the **SMS Spam Collection** dataset:

- **Kaggle**: https://www.kaggle.com/datasets/uciml/sms-spam-collection-dataset
- Download `spam.csv` and place it at: `backend/data/spam.csv`

The file should have these columns:
| Column | Description |
|--------|-------------|
| `v1`   | Label (`ham` or `spam`) |
| `v2`   | Message text |

---

### 2. Install Python Dependencies

```bash
cd backend
# Create virtual environment (one-time)
python -m venv venv

# Activate it  (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

> Requires Python 3.10 or higher.

---

### 3. Train the Model (Run Once)

```bash
cd backend
.\venv\Scripts\Activate.ps1   # if not already activated
python model/train.py
```

This will:
- Load `backend/data/spam.csv`
- Train a TF-IDF + Naive Bayes pipeline
- Print accuracy and classification report
- Save the model to `backend/model/spam_model.pkl`

Expected output:
```
[train] Dataset loaded: 5572 samples
[train] Test accuracy: 98.47%
[train] Model saved to 'backend/model/spam_model.pkl'
[train] Done!
```

---

### 4. Start the Flask Server

```bash
cd backend
.\venv\Scripts\Activate.ps1   # if not already activated
python app.py
```

Server starts at: `http://localhost:5000`

Available endpoints:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /predict` | JSON `{ "text": "…" }` | Classify text |
| `POST /upload` | `multipart/form-data` file | Classify .txt or .eml file |
| `GET /health` | — | Health check |

---

### 5. Open the Frontend

Simply open `frontend/index.html` in your browser:
- Double-click the file, **OR**
- Use VS Code **Live Server** extension for best results

> No build step required. The frontend is plain HTML/CSS/JS.

---

## API Response Format

Both `/predict` and `/upload` return:

```json
{
  "prediction": "spam",
  "confidence": 94.7,
  "reasons": [
    "Spam keywords detected: free, winner, claim",
    "Urgency phrases detected: act now, limited time",
    "1 suspicious link found (e.g. http://bit.ly/abc)"
  ],
  "explanation": {
    "spam_keywords":    ["free", "winner", "claim"],
    "urgency_phrases":  ["act now", "limited time"],
    "suspicious_links": ["http://bit.ly/abc"]
  }
}
```

---

## Highlight Colours

| Colour | Meaning |
|--------|---------|
| 🟡 Yellow | Spam keywords |
| 🟠 Orange | Urgency phrases |
| 🔴 Red | Suspicious links |

---

## Error Responses

| Situation | HTTP | Error message |
|-----------|------|--------------|
| Empty input | 400 | `Input text cannot be empty.` |
| Unsupported file | 400 | `Only .txt and .eml files are supported.` |
| Model not trained | 503 | `Model not loaded. Run train.py first.` |
| Server error | 500 | `Internal server error.` |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, Vanilla CSS (dark mode, glassmorphism), Vanilla JS |
| Backend | Python 3.10+, Flask, Flask-CORS |
| ML | scikit-learn — TF-IDF + MultinomialNB |
| Model storage | joblib `.pkl` |
| File parsing | Python `email` stdlib |
| Dataset | SMS Spam Collection (`spam.csv`) |

---

## Quick Test (curl)

```bash
# Test text prediction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"Congratulations! You have won a FREE prize. Click here NOW!\"}"

# Test file upload
curl -X POST http://localhost:5000/upload \
  -F "file=@sample_spam.txt"
```
