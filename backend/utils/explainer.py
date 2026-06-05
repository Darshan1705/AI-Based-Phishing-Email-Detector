"""
explainer.py
Three-tier explanation engine that scans email text for:
  1. Spam keywords   → yellow highlight
  2. Urgency phrases → orange highlight
  3. Suspicious URLs → red highlight
"""

import re

# ---------------------------------------------------------------------------
# Word / phrase lists
# ---------------------------------------------------------------------------

SPAM_KEYWORDS = [
    "free", "winner", "winners", "won", "win", "prize", "prizes",
    "claim", "congratulations", "congrats", "cash", "money",
    "earn", "income", "reward", "rewards", "bonus", "bonuses",
    "offer", "offers", "deal", "deals", "discount", "discounts",
    "buy now", "click here", "click below", "order now",
    "subscribe", "unsubscribe", "guaranteed", "100%", "risk-free",
    "no cost", "no fee", "no obligation", "credit card", "investment",
    "million", "billion", "lottery", "selected", "chosen",
    "promotion", "promotional", "special offer", "exclusive",
    "double your", "triple your", "make money", "work from home",
    "extra income", "financial freedom", "get paid", "instant cash",
    "money back", "refund guaranteed", "satisfaction guaranteed",
    "dear friend", "dear winner", "dear beneficiary",
    "bank account", "wire transfer", "western union",
    "nigerian", "inheritance", "beneficiary",
]

URGENCY_PHRASES = [
    "act now", "act immediately", "urgent", "urgently",
    "limited time", "limited offer", "hurry", "hurry up",
    "don't miss", "do not miss", "don't wait", "do not wait",
    "expires", "expiring", "expiry", "deadline",
    "last chance", "final notice", "final warning",
    "today only", "ends today", "ending soon",
    "immediate", "immediately", "respond now",
    "you must", "you have been", "account suspended",
    "verify now", "confirm now", "validate now",
    "your account will be", "your account has been",
]

# TLDs / patterns that signal suspicious links
_SUSPICIOUS_TLDS = re.compile(
    r"https?://[^\s]+\.(?:xyz|tk|cc|top|club|online|site|info|biz|loan|work|click)[^\s]*",
    re.IGNORECASE,
)
_SHORT_URLS = re.compile(
    r"https?://(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|ow\.ly|is\.gd|buff\.ly|rb\.gy|short\.io)[^\s]*",
    re.IGNORECASE,
)
_HTTP_ONLY = re.compile(r"http://[^\s]+", re.IGNORECASE)   # non-HTTPS
_PORT_URL = re.compile(r"https?://[^\s]+:\d{2,5}[^\s]*", re.IGNORECASE)  # URL with port


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def explain(text: str) -> dict:
    """
    Analyse *text* and return matched evidence for each explanation category.

    Returns
    -------
    dict
        {
            "spam_keywords":    list[str],
            "urgency_phrases":  list[str],
            "suspicious_links": list[str],
        }
    """
    lower = text.lower()

    # --- spam keywords ---
    found_keywords = []
    for kw in SPAM_KEYWORDS:
        pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
        if pattern.search(text):
            found_keywords.append(kw)

    # --- urgency phrases ---
    found_urgency = []
    for phrase in URGENCY_PHRASES:
        pattern = re.compile(r'\b' + re.escape(phrase) + r'\b', re.IGNORECASE)
        if pattern.search(text):
            found_urgency.append(phrase)

    # --- suspicious links ---
    found_links = []
    for pattern in [_SUSPICIOUS_TLDS, _SHORT_URLS, _HTTP_ONLY, _PORT_URL]:
        matches = pattern.findall(text)
        found_links.extend(matches)
    # deduplicate while preserving order
    seen = set()
    deduped_links = []
    for link in found_links:
        if link not in seen:
            seen.add(link)
            deduped_links.append(link)

    return {
        "spam_keywords":   list(dict.fromkeys(found_keywords)),   # preserve order, dedupe
        "urgency_phrases": list(dict.fromkeys(found_urgency)),
        "suspicious_links": deduped_links,
    }


def build_reasons(explanation: dict) -> list[str]:
    """Convert the explanation dict into human-readable reason strings."""
    reasons = []

    if explanation["spam_keywords"]:
        kws = ", ".join(explanation["spam_keywords"][:8])  # cap display length
        reasons.append(f"Spam keywords detected: {kws}")

    if explanation["urgency_phrases"]:
        ups = ", ".join(explanation["urgency_phrases"][:5])
        reasons.append(f"Urgency phrases detected: {ups}")

    if explanation["suspicious_links"]:
        count = len(explanation["suspicious_links"])
        sample = explanation["suspicious_links"][0]
        reasons.append(
            f"{count} suspicious link{'s' if count > 1 else ''} found "
            f"(e.g. {sample[:60]}{'…' if len(sample) > 60 else ''})"
        )

    return reasons
