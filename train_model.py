"""Train and evaluate URLShield AI models on the demo dataset."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from url_features import FEATURE_NAMES, extract_features

ROOT = Path(__file__).parent


def build_dataset(data_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    data = pd.read_csv(data_path)
    features = pd.DataFrame([extract_features(url) for url in data["url"]])[FEATURE_NAMES]
    return features, data["label"]


def evaluate(name: str, model: Pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> dict[str, float | str]:
    predictions = model.predict(x_test)
    return {
        "model": name,
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "f1": f1_score(y_test, predictions, zero_division=0),
    }


def main() -> None:
    x, y = build_dataset(ROOT / "data.csv")
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.25, random_state=42, stratify=y
    )
    candidates = {
        "Logistic Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000, random_state=42)),
        ]),
        "Random Forest": Pipeline([
            ("model", RandomForestClassifier(n_estimators=250, random_state=42, class_weight="balanced")),
        ]),
    }
    results = []
    for name, model in candidates.items():
        model.fit(x_train, y_train)
        results.append(evaluate(name, model, x_test, y_test))
    results.sort(key=lambda row: (row["f1"], row["recall"], row["accuracy"]), reverse=True)
    selected_name = str(results[0]["model"])
    selected_model = candidates[selected_name].fit(x, y)
    selected_predictions = selected_model.predict(x_test)
    final_metrics = results[0].copy()
    bundle = {
        "model": selected_model,
        "feature_names": FEATURE_NAMES,
        "model_name": selected_name,
        "dataset_size": len(data := pd.read_csv(ROOT / "data.csv")),
        "metrics": final_metrics,
        "confusion_matrix": confusion_matrix(y_test, selected_predictions).tolist(),
        "feature_importance": dict(zip(FEATURE_NAMES, _feature_importance(selected_model))),
        "data_note": "Synthetic/demo dataset; metrics are not real-world performance.",
    }
    joblib.dump(bundle, ROOT / "model.pkl")

    print("Evaluation on the held-out demo split (synthetic data; not real-world performance):")
    for result in results:
        print(
            f"{result['model']}: accuracy={result['accuracy']:.2f}, "
            f"precision={result['precision']:.2f}, recall={result['recall']:.2f}, f1={result['f1']:.2f}"
        )
    print(f"Selected model: {selected_name}")
    print(f"Saved: {ROOT / 'model.pkl'}")


def _feature_importance(model: Pipeline) -> list[float]:
    estimator = model[-1]
    if hasattr(estimator, "coef_"):
        return [abs(float(value)) for value in estimator.coef_[0]]
    return [float(value) for value in estimator.feature_importances_]


if __name__ == "__main__":
    main()
