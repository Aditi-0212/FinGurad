"""
Duplicate invoice detection.

Why not exact invoice-number matching alone: the spec explicitly calls
out that duplicated invoices often arrive with a *different* invoice
number (resubmission, re-keying, separate vendor systems). So the real
signal is: same vendor, very similar amount, close together in time,
similar description — not "same invoice_id".

Approach: for each vendor, compare every pair of their transactions
within a configurable time window. Score similarity using:
  - amount closeness (within a % tolerance)
  - date proximity (within N days)
  - description similarity (fuzzy string match via rapidfuzz)
Combine into a similarity score; flag pairs above a threshold.

This is O(n^2) per vendor, which is fine at this dataset's scale
(a few dozen transactions per vendor). At real enterprise scale you'd
bucket by (vendor, amount range, week) first to cut comparisons down -
noted here for the "what alternatives exist" interview question.
"""

from dataclasses import dataclass, field

import pandas as pd
from rapidfuzz import fuzz

AMOUNT_TOLERANCE_PCT = 0.05  # amounts within 5% of each other count as "close"
DATE_WINDOW_DAYS = 5  # only compare transactions within this many days of each other
SIMILARITY_THRESHOLD = 70  # 0-100 combined score; pairs at/above this are flagged


@dataclass
class DuplicateMatch:
    transaction_id_a: str
    transaction_id_b: str
    vendor_id: str
    amount_a: float
    amount_b: float
    date_a: str
    date_b: str
    days_apart: int
    amount_diff_pct: float
    description_similarity: float
    combined_score: float
    reasons: list[str] = field(default_factory=list)


def _score_pair(row_a: pd.Series, row_b: pd.Series) -> DuplicateMatch | None:
    amount_diff_pct = abs(row_a["amount"] - row_b["amount"]) / max(row_a["amount"], row_b["amount"])
    days_apart = abs((row_a["date"] - row_b["date"]).days)

    if days_apart > DATE_WINDOW_DAYS:
        return None

    desc_similarity = fuzz.token_sort_ratio(str(row_a["description"]), str(row_b["description"]))

    # Weighted combination: amount closeness matters most, then description, then recency.
    amount_score = max(0.0, 100 - (amount_diff_pct / AMOUNT_TOLERANCE_PCT) * 100) if amount_diff_pct <= AMOUNT_TOLERANCE_PCT * 3 else 0
    date_score = max(0.0, 100 - (days_apart / DATE_WINDOW_DAYS) * 100)
    combined = round(0.5 * amount_score + 0.3 * desc_similarity + 0.2 * date_score, 1)

    if combined < SIMILARITY_THRESHOLD:
        return None

    reasons = []
    if amount_diff_pct <= AMOUNT_TOLERANCE_PCT:
        reasons.append(f"Amounts within {amount_diff_pct*100:.1f}% of each other")
    if days_apart <= 3:
        reasons.append(f"Dated only {days_apart} day(s) apart")
    if desc_similarity >= 85:
        reasons.append("Description text nearly identical")
    if row_a["invoice_id"] != row_b["invoice_id"]:
        reasons.append("Different invoice numbers — would be missed by exact invoice-ID matching")

    return DuplicateMatch(
        transaction_id_a=row_a["transaction_id"],
        transaction_id_b=row_b["transaction_id"],
        vendor_id=row_a["vendor_id"],
        amount_a=row_a["amount"],
        amount_b=row_b["amount"],
        date_a=row_a["date"].date().isoformat(),
        date_b=row_b["date"].date().isoformat(),
        days_apart=days_apart,
        amount_diff_pct=round(amount_diff_pct * 100, 2),
        description_similarity=desc_similarity,
        combined_score=combined,
        reasons=reasons,
    )


def find_duplicate_invoices(transactions_df: pd.DataFrame) -> list[DuplicateMatch]:
    """transactions_df must have columns: transaction_id, vendor_id, date (datetime),
    amount, description, invoice_id. Returns matches sorted by combined_score desc."""
    matches: list[DuplicateMatch] = []
    for vendor_id, group in transactions_df.groupby("vendor_id"):
        group = group.reset_index(drop=True)
        n = len(group)
        for i in range(n):
            for j in range(i + 1, n):
                match = _score_pair(group.loc[i], group.loc[j])
                if match:
                    matches.append(match)
    return sorted(matches, key=lambda m: m.combined_score, reverse=True)
