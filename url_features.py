"""Feature engineering for URLShield AI."""

from __future__ import annotations

import ipaddress
import math
import re
from collections import Counter
from typing import Any
from urllib.parse import parse_qs, urlparse

SUSPICIOUS_KEYWORDS = {
    "account", "authenticate", "authentication", "bank", "billing", "confirm",
    "credential", "fake", "fraud", "login", "malicious", "password", "payment",
    "phishing", "recover", "scam", "secure", "signin", "unlock", "update",
    "verify", "wallet",
}
SUSPICIOUS_TLDS = {".tk", ".ml", ".ga", ".cf", ".gq", ".top", ".xyz", ".zip"}
FEATURE_NAMES = [
    "url_length", "hostname_length", "path_length", "dot_count", "hyphen_count",
    "slash_count", "digit_count", "special_char_count", "query_parameter_count",
    "subdomain_count", "uses_https", "has_ip_address", "has_at_symbol",
    "has_encoded_chars", "suspicious_keyword_count", "suspicious_tld", "url_entropy",
]


def _safe_parse(url: str):
    candidate = url.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", candidate):
        candidate = f"http://{candidate}"
    return candidate, urlparse(candidate)


def normalize_url(url: str) -> str:
    """Normalize a user-entered URL without contacting the destination."""
    candidate, parsed = _safe_parse(str(url or "").strip())
    return parsed.geturl() if parsed.netloc else candidate


def _is_ip(hostname: str) -> bool:
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def extract_features(url: str) -> dict[str, Any]:
    """Return stable numeric URL signals and safe parsed components."""
    raw = str(url or "").strip()
    candidate, parsed = _safe_parse(raw)
    hostname = (parsed.hostname or "").lower()
    path = parsed.path or ""
    query = parsed.query or ""
    lowered = candidate.lower()
    labels = [label for label in hostname.split(".") if label]
    keyword_count = sum(keyword in lowered for keyword in SUSPICIOUS_KEYWORDS)
    tld = f".{labels[-1]}" if labels else ""
    is_ip = _is_ip(hostname)
    subdomain = ".".join(labels[:-2]) if len(labels) > 2 and not is_ip else "none"
    try:
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
    except ValueError:
        port = "invalid"

    features: dict[str, Any] = {
        "url_length": len(raw),
        "hostname_length": len(hostname),
        "path_length": len(path),
        "dot_count": raw.count("."),
        "hyphen_count": raw.count("-"),
        "slash_count": raw.count("/"),
        "digit_count": sum(character.isdigit() for character in raw),
        "special_char_count": sum(not character.isalnum() for character in raw),
        "query_parameter_count": len(parse_qs(query, keep_blank_values=True)),
        "subdomain_count": max(len(labels) - 2, 0),
        "uses_https": int(parsed.scheme.lower() == "https"),
        "has_ip_address": int(is_ip),
        "has_at_symbol": int("@" in raw),
        "has_encoded_chars": int(bool(re.search(r"%[0-9a-fA-F]{2}", raw))),
        "suspicious_keyword_count": keyword_count,
        "suspicious_tld": int(tld in SUSPICIOUS_TLDS),
        "url_entropy": round(_entropy(raw), 4),
    }
    features.update({
        "protocol": parsed.scheme or "unknown",
        "domain": hostname or "unavailable",
        "path": path or "/",
        "query": query or "none",
        "fragment": parsed.fragment or "none",
        "normalized_url": candidate,
        "subdomain": subdomain,
        "tld": tld or "unknown",
        "port": port,
        "has_punycode": int("xn--" in hostname),
        "suspicious_keywords": ", ".join(sorted(keyword for keyword in SUSPICIOUS_KEYWORDS if keyword in lowered)) or "none",
    })
    return features
