# URLShield AI

## Explainable Phishing URL Risk Analyzer

URLShield AI is a compact cybersecurity machine-learning application that turns URL structure into an interpretable risk assessment. It extracts security signals, compares two classifiers, scores a URL from 0 to 100, and shows the evidence behind the result in a Streamlit dashboard.

> The included `data.csv` is clearly labeled demo/synthetic data for portfolio demonstration. Its metrics must not be interpreted as real-world phishing detection performance.

## Problem Statement

Phishing URLs often imitate familiar services while hiding risky structure in long paths, misleading subdomains, encoded characters, or IP addresses. A useful first-pass tool should be fast and explainable, while leaving the final decision to a human or a stronger security system.

## Solution And Features

- URL parsing that safely handles missing schemes and malformed input
- 17 engineered URL features, including entropy, domain structure, HTTPS, IP addresses, keywords, and TLD signals
- Logistic Regression versus Random Forest evaluation using accuracy, precision, recall, and F1-score
- Persisted scikit-learn model with joblib
- AI Risk Score, five risk levels, confidence, and analysis time
- Evidence-based explanations and local feature-impact chart
- Plotly risk gauge and expandable URL breakdown
- Sidebar navigation for Scanner, Model insights, and Methodology views
- URL anatomy, parsed domain intelligence, security checklist, session scan history, and JSON/CSV report downloads
- Persisted model metadata including confusion matrix and top feature importance
- Friendly handling for empty input, invalid URLs, missing model, and prediction failures

## Tech Stack

Python 3.11+, pandas, NumPy, scikit-learn, joblib, Streamlit, and Plotly.

## ML Workflow

1. Read labeled URLs from `data.csv`.
2. Apply the same feature extractor used at prediction time.
3. Split the demo data into train and test portions.
4. Compare Logistic Regression and Random Forest.
5. Select the highest F1-score, then refit it on all demo rows.
6. Save the model and feature order to `model.pkl`.

The dashboard combines the classifier's phishing-class score with a small, transparent boost for especially clear structural signals such as an IP address, `@`, or suspicious TLD. This is an AI Risk Score, not a guaranteed probability of maliciousness.

## Feature Engineering

Numeric signals cover URL, hostname, and path lengths; punctuation and digit counts; query parameters; subdomains; HTTPS; IP address and `@` detection; percent encoding; suspicious keyword/TLD flags; and Shannon-style URL entropy. `urllib.parse` and `ipaddress` provide standard-library parsing.

## Explainable AI

`explain.py` derives explanations from observed feature values, so it never invents evidence. The current compact model uses feature-importance-style evidence rules for reliable UI explanations. The persisted model is structured so SHAP can be added later when a larger real dataset justifies it.

## Project Structure

```text
URLShield-AI/
├── app.py             # Streamlit dashboard
├── run.py             # one-command launcher
├── url_features.py    # URL parsing and feature engineering
├── train_model.py     # model comparison and persistence
├── predict.py         # validation and inference
├── explain.py         # evidence-based explanations
├── data.csv           # small synthetic demo dataset
├── model.pkl          # generated trained model
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation And Run

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python train_model.py
streamlit run app.py
```

## One-Command Launch

From the project folder, this command installs missing dependencies, retrains `model.pkl`, and starts the dashboard:

```powershell
python run.py
```

Open `http://localhost:8501` when Streamlit starts. Stop the server with `Ctrl+C`.

Use the demo URLs shown in the app, or try `https://example.com/`. Retrain after replacing `data.csv` with a compatible labeled dataset containing `url` and `label` columns.

The scanner accepts URLs with or without a scheme, normalizes them locally, and never contacts the destination. The Model insights view reports metrics from the current synthetic/demo training run and is explicitly not a production benchmark.

## Limitations

- Synthetic data is tiny and intentionally illustrative, so it cannot establish production accuracy.
- URL-only signals miss page content, redirects, domain age, DNS, reputation, and user context.
- Attackers can change URL patterns, and HTTPS alone does not make a site trustworthy.
- The model is a triage aid, not an automated blocking decision.

## Future Improvements

Use a larger, ethically sourced and time-split real dataset; calibrate scores; add redirect and domain-age enrichment; add SHAP summary and per-URL plots; monitor drift; and evaluate false-positive cost before deployment.
