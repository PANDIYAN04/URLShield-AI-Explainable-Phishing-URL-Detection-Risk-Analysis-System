"""Evidence-based explanations for URLShield AI predictions."""

from __future__ import annotations

from typing import Any


def explain_result(result: dict[str, Any]) -> list[dict[str, str]]:
    """Return only explanations supported by extracted URL features."""
    features = result["features"]
    explanations: list[dict[str, str]] = []

    def add(impact: str, text: str, weight: int) -> None:
        explanations.append({"impact": impact, "text": text, "weight": str(weight)})

    if features["has_ip_address"]:
        add("HIGH IMPACT", "IP address detected instead of a domain name", 5)
    if features["has_at_symbol"]:
        add("HIGH IMPACT", "@ symbol can obscure the true destination", 5)
    if features["suspicious_tld"]:
        add("HIGH IMPACT", "Suspicious top-level domain detected", 4)
    if features["url_length"] > 90:
        add("MEDIUM IMPACT", "Unusually long URL structure", 3)
    explicit_test_tokens = {"malicious", "phishing", "scam", "fraud", "fake"}
    observed_tokens = set(features["suspicious_keywords"].split(", "))
    if observed_tokens & explicit_test_tokens:
        add("HIGH IMPACT", f"Explicit suspicious test token detected: {features['suspicious_keywords']}", 5)
    elif features["suspicious_keyword_count"]:
        keyword_text = features["suspicious_keywords"]
        add("MEDIUM IMPACT", f"Suspicious URL token detected: {keyword_text}", 3)
    if features["subdomain_count"] > 2:
        add("MEDIUM IMPACT", "Multiple subdomains increase domain complexity", 2)
    if features["has_encoded_chars"]:
        add("LOW IMPACT", "Encoded characters make the URL harder to inspect", 2)
    if features["uses_https"] and not features["has_ip_address"]:
        add("LOW RISK SIGNAL", "HTTPS is enabled", -2)
    if features["subdomain_count"] <= 2 and not features["has_ip_address"]:
        add("LOW RISK SIGNAL", "Normal domain structure", -1)
    if not explanations:
        add("LOW RISK SIGNAL", "No strong URL-based warning signals detected", -1)
    return sorted(explanations, key=lambda item: int(item["weight"]), reverse=True)
