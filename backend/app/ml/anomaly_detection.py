"""
Transaction anomaly detection via Isolation Forest.

Why Isolation Forest specifically: it doesn't need labeled fraud examples
(we don't have any in a real deployment), it handles the mixed-scale
numeric features here well, and it's fast enough to re-run on every new
batch of transactions. The alternative considered was pure statistical
thresholds (z-score on amount deviation) — simpler and more explainable,
but misses multi-feature combinations (e.g. a normal amount at an
abnormal frequency for a new vendor). We use both: Isolation Forest for
the overall anomaly score, plus explicit statistical signals (vendor
deviation, frequency) as human-readable evidence, so the AI layer in
Phase 8 never has to explain a black-box score alone.

Features per transaction:
  - amount
  - amount_deviation_ratio: amount / vendor's historical average
  - vendor_age (months)
  - vendor_txn_count: how many transactions this vendor has in the dataset
  - day_of_week (captures unusual timing patterns)

Output: each transaction gets an anomaly_score (0-100, higher = more
anomalous) and a list of human-readable evidence strings.
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

CONTAMINATION = 0.08  # expect ~8% of transactions to be anomalous; tuned to this dataset's injected rate


@dataclass
class AnomalyResult:
    transaction_id: str
    vendor_id: str
    amount: float
    anomaly_score: int  # 0-100, higher = more anomalous
    is_anomaly: bool
    evidence: list[str] = field(default_factory=list)


def _build_features(transactions_df: pd.DataFrame, vendors_df: pd.DataFrame) -> pd.DataFrame:
    df = transactions_df.merge(
        vendors_df[["vendor_id", "vendor_age", "average_transaction"]],
        on="vendor_id",
        how="left",
        suffixes=("", "_vendor"),
    )
    df["amount_deviation_ratio"] = df["amount"] / df["average_transaction"].replace(0, np.nan)
    df["amount_deviation_ratio"] = df["amount_deviation_ratio"].fillna(1.0)
    df["day_of_week"] = pd.to_datetime(df["date"]).dt.dayofweek

    vendor_txn_counts = df.groupby("vendor_id")["transaction_id"].transform("count")
    df["vendor_txn_count"] = vendor_txn_counts

    return df


def detect_anomalies(transactions_df: pd.DataFrame, vendors_df: pd.DataFrame) -> list[AnomalyResult]:
    df = _build_features(transactions_df, vendors_df)

    feature_cols = ["amount", "amount_deviation_ratio", "vendor_age", "vendor_txn_count", "day_of_week"]
    X = df[feature_cols].fillna(0).values

    model = IsolationForest(contamination=CONTAMINATION, random_state=42, n_estimators=200)
    raw_scores = model.fit_predict(X)  # -1 = anomaly, 1 = normal
    decision_scores = model.decision_function(X)  # lower = more anomalous

    # Normalize decision_function output to a 0-100 "risk score" for human readability.
    min_s, max_s = decision_scores.min(), decision_scores.max()
    normalized = 100 * (max_s - decision_scores) / (max_s - min_s + 1e-9)

    results = []
    for i, row in df.iterrows():
        is_anom = raw_scores[i] == -1
        score = int(round(normalized[i]))

        evidence = []
        if row["amount_deviation_ratio"] >= 3.0:
            evidence.append(
                f"Amount is {row['amount_deviation_ratio']:.1f}x vendor {row['vendor_id']}'s historical average"
            )
        elif row["amount_deviation_ratio"] >= 1.8:
            evidence.append(
                f"Amount is {row['amount_deviation_ratio']:.1f}x higher than vendor's typical transaction"
            )
        if row["vendor_age"] < 3:
            evidence.append(f"Vendor was onboarded only {int(row['vendor_age'])} month(s) ago")
        if row["vendor_txn_count"] <= 2:
            evidence.append("Vendor has very few transactions on record — limited history to compare against")

        if is_anom and not evidence:
            evidence.append("Flagged by anomaly model based on a combination of amount, timing, and vendor factors")

        results.append(
            AnomalyResult(
                transaction_id=row["transaction_id"],
                vendor_id=row["vendor_id"],
                amount=row["amount"],
                anomaly_score=score,
                is_anomaly=is_anom,
                evidence=evidence,
            )
        )

    return sorted(results, key=lambda r: r.anomaly_score, reverse=True)
