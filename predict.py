"""Prediction service for the URLShield AI dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from url_features import FEATURE_NAMES, extract_features, normalize_url

MODEL_PATH = Path(__file__).parent / "model.pkl"


def _risk_level(score: int) -> str:
    if score <= 20:
        return "LOW RISK"
    if score <= 40:
        return "GUARDED"
    if score <= 60:
        return "SUSPICIOUS"
    if score <= 80:
        return "HIGH RISK"
    return "CRITICAL"


def analyze_url(url: str) -> dict[str, Any]:
    """Analyze a URL and return model output plus the engineered feature row."""
    if not str(url or "").strip():
        raise ValueError("Please enter a URL to analyze.")
    if len(str(url).strip()) > 2048:
        raise ValueError("This URL is too long to analyze safely.")
    normalized_url = normalize_url(url)
    features = extract_features(normalized_url)
    if features["domain"] == "unavailable":
        raise ValueError("The URL does not contain a recognizable domain.")
    if not MODEL_PATH.exists():
        raise FileNotFoundError("model.pkl is missing. Run `python train_model.py` first.")

    bundle = joblib.load(MODEL_PATH)
    model = bundle["model"]
    feature_names = bundle.get("feature_names", FEATURE_NAMES)
    row = pd.DataFrame([[features[name] for name in feature_names]], columns=feature_names)
    prediction = int(model.predict(row)[0])
    probabilities = model.predict_proba(row)[0]
    confidence = float(max(probabilities))
    raw_score = float(probabilities[1] * 100)
    # Lightweight domain heuristics prevent a demo model from hiding clear signals.
    signal_boost = min(
        40,
        features["has_ip_address"] * 20
        + features["has_at_symbol"] * 10
        + features["suspicious_tld"] * 8
        + features["suspicious_keyword_count"] * 20,
    )
    risk_score = int(round(min(100, max(0, raw_score + signal_boost))))

    return {
        "url": str(url).strip(),
        "normalized_url": normalized_url,
        "prediction": prediction,
        "benign_probability": float(probabilities[0]),
        "phishing_probability": float(probabilities[1]),
        "classification": _risk_level(risk_score),
        "confidence": confidence,
        "risk_score": risk_score,
        "features": features,
        "feature_names": feature_names,
        "model_name": bundle.get("model_name", "trained classifier"),
    }
