"""
Receivables monitoring: identifies overdue invoices, prioritizes by
value + days overdue, and flags customers with a repeated late-payment
pattern. Again deliberately arithmetic/rules-based, not ML — aging
buckets are a standard, auditable finance concept; there's no benefit
to making this a black box.
"""

from dataclasses import dataclass
from datetime import date

import pandas as pd

HIGH_PRIORITY_DAYS_OVERDUE = 30
HIGH_PRIORITY_AMOUNT = 100_000
REPEAT_LATE_PAYER_THRESHOLD = 2  # customers with > this many overdue invoices are flagged


@dataclass
class ReceivableStatus:
    invoice_id: str
    customer: str
    amount: float
    due_date: str
    days_overdue: int
    payment_status: str
    priority: str  # LOW / MEDIUM / HIGH


def analyze_receivables(receivables_df: pd.DataFrame, as_of: date | None = None) -> list[ReceivableStatus]:
    as_of = as_of or date.today()
    results = []

    for _, row in receivables_df.iterrows():
        due = pd.to_datetime(row["due_date"]).date()
        days_overdue = max(0, (as_of - due).days) if row["payment_status"] != "Paid" else 0

        if row["payment_status"] == "Paid":
            priority = "LOW"
        elif days_overdue >= HIGH_PRIORITY_DAYS_OVERDUE and row["amount"] >= HIGH_PRIORITY_AMOUNT:
            priority = "HIGH"
        elif days_overdue >= HIGH_PRIORITY_DAYS_OVERDUE or row["amount"] >= HIGH_PRIORITY_AMOUNT:
            priority = "MEDIUM"
        elif days_overdue > 0:
            priority = "LOW"
        else:
            priority = "LOW"

        results.append(
            ReceivableStatus(
                invoice_id=row["invoice_id"],
                customer=row["customer"],
                amount=row["amount"],
                due_date=due.isoformat(),
                days_overdue=days_overdue,
                payment_status=row["payment_status"],
                priority=priority,
            )
        )

    return sorted(results, key=lambda r: (r.priority != "HIGH", r.priority != "MEDIUM", -r.days_overdue))


def find_repeated_late_payers(receivables_df: pd.DataFrame, as_of: date | None = None) -> list[dict]:
    as_of = as_of or date.today()
    df = receivables_df.copy()
    df["due_date_parsed"] = pd.to_datetime(df["due_date"]).dt.date
    df["is_overdue"] = (df["payment_status"] == "Overdue") | (
        (df["payment_status"] != "Paid") & (df["due_date_parsed"] < as_of)
    )

    overdue_counts = df[df["is_overdue"]].groupby("customer").size()
    repeat_offenders = overdue_counts[overdue_counts > REPEAT_LATE_PAYER_THRESHOLD]

    return [
        {"customer": customer, "overdue_invoice_count": int(count)}
        for customer, count in repeat_offenders.sort_values(ascending=False).items()
    ]
