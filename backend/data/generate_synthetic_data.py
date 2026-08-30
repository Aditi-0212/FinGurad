"""
Synthetic financial dataset generator for FinGuard AI.

Why this exists: we cannot use real company financial data, but the
detection logic (duplicate invoices, anomalous transactions, budget
overruns, overdue receivables) needs realistic data WITH real anomalies
baked in — not hardcoded results — so Phase 4's ML/rules can actually
discover them rather than us faking the output.

This script is deterministic (fixed random seed) so re-running it
produces the exact same dataset, and every injected anomaly is logged
to anomalies_manifest.md with the reason it was injected. That manifest
is the ground truth we test detection accuracy against in Phase 11 —
it is NOT read by the detection code itself.

Run:
    python generate_synthetic_data.py

Outputs (written to this directory):
    vendors.csv
    transactions.csv
    budgets.csv
    receivables.csv
    anomalies_manifest.md
"""

import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

OUTPUT_DIR = "."  # run from backend/data/

DEPARTMENTS = ["Marketing", "Engineering", "Operations", "Sales", "HR", "Finance"]
CATEGORIES = {
    "Marketing": ["Advertising", "Events", "Content", "Software Subscriptions"],
    "Engineering": ["Cloud Infrastructure", "Software Licenses", "Hardware", "Contractors"],
    "Operations": ["Facilities", "Utilities", "Logistics", "Office Supplies"],
    "Sales": ["Travel", "Client Entertainment", "Software Subscriptions", "Commissions"],
    "HR": ["Recruiting", "Training", "Benefits Admin", "Payroll Services"],
    "Finance": ["Audit Fees", "Software Subscriptions", "Banking Fees", "Consulting"],
}
PAYMENT_METHODS = ["Bank Transfer", "Corporate Card", "Cheque", "ACH"]
INDUSTRIES = ["IT Services", "Logistics", "Consulting", "Manufacturing", "Marketing Agency", "SaaS"]

START_DATE = date(2025, 3, 1)
END_DATE = date(2025, 8, 31)
NUM_VENDORS = 45
NUM_BASE_TRANSACTIONS = 650

manifest_entries = []  # collected as we inject anomalies, written to anomalies_manifest.md


def log_anomaly(category: str, record_id: str, reason: str):
    manifest_entries.append({"category": category, "record_id": record_id, "reason": reason})


def random_date(start: date, end: date) -> date:
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


# ---------------------------------------------------------------------------
# 1. VENDORS
# ---------------------------------------------------------------------------

def generate_vendors(n: int) -> pd.DataFrame:
    vendors = []
    for i in range(1, n + 1):
        vendor_id = f"VEND-{i:04d}"
        # Vendor age in months since onboarding; most are established,
        # a handful are brand new (used later for "newly created vendor" anomaly)
        vendor_age_months = random.randint(6, 96)
        avg_txn = round(np.random.lognormal(mean=8.5, sigma=0.8), 2)  # skewed, realistic spread
        vendors.append(
            {
                "vendor_id": vendor_id,
                "vendor_name": f"{random.choice(['ABC', 'Prime', 'Northstar', 'Bluewave', 'Summit', 'Vertex', 'Anchor', 'Redline', 'Silverline', 'Crestview'])} "
                f"{random.choice(['Supplies', 'Services', 'Solutions', 'Traders', 'Enterprises', 'Partners', 'Group', 'Industries'])}",
                "vendor_age": vendor_age_months,
                "industry": random.choice(INDUSTRIES),
                "risk_level": "LOW",  # placeholder, recalculated below after anomalies known
                "total_transactions": 0,  # filled in after transactions are generated
                "average_transaction": avg_txn,
            }
        )
    df = pd.DataFrame(vendors)

    # Inject 3 deliberately "newly created" vendors (age < 2 months) — used later
    # for the "vendor was recently created" evidence signal.
    new_vendor_indices = random.sample(range(len(df)), 3)
    for idx in new_vendor_indices:
        df.loc[idx, "vendor_age"] = random.randint(0, 2)
        log_anomaly(
            "vendor_recently_created",
            df.loc[idx, "vendor_id"],
            f"Vendor age set to {df.loc[idx, 'vendor_age']} months to simulate a newly onboarded vendor "
            "with limited transaction history — a common fraud/error risk signal.",
        )
    return df


# ---------------------------------------------------------------------------
# 2. TRANSACTIONS (with injected anomalies)
# ---------------------------------------------------------------------------

def generate_base_transactions(vendors_df: pd.DataFrame, n: int) -> list[dict]:
    transactions = []
    for i in range(1, n + 1):
        vendor_row = vendors_df.sample(1).iloc[0]
        dept = random.choice(DEPARTMENTS)
        category = random.choice(CATEGORIES[dept])
        txn_date = random_date(START_DATE, END_DATE)
        # Amount clusters around the vendor's average with normal variance
        amount = max(500, round(np.random.normal(loc=vendor_row["average_transaction"], scale=vendor_row["average_transaction"] * 0.25), 2))
        transactions.append(
            {
                "transaction_id": f"TXN-{i:05d}",
                "date": txn_date.isoformat(),
                "vendor_id": vendor_row["vendor_id"],
                "vendor_name": vendor_row["vendor_name"],
                "department": dept,
                "category": category,
                "amount": amount,
                "payment_method": random.choice(PAYMENT_METHODS),
                "invoice_id": f"INV-{i:05d}",
                "description": f"{category} - {vendor_row['vendor_name']}",
                "approval_status": random.choices(["Approved", "Pending", "Approved", "Approved"], k=1)[0],
            }
        )
    return transactions


def inject_duplicate_invoices(transactions: list[dict], num_pairs: int = 8) -> list[dict]:
    """Create near-duplicate transactions: same vendor/amount, close dates,
    slightly different invoice numbers or descriptions — the kind fuzzy
    matching should catch but exact invoice-number matching would miss."""
    next_id = len(transactions) + 1
    for _ in range(num_pairs):
        original = random.choice(transactions)
        dup_date = (date.fromisoformat(original["date"]) + timedelta(days=random.randint(1, 3))).isoformat()
        duplicate = {
            "transaction_id": f"TXN-{next_id:05d}",
            "date": dup_date,
            "vendor_id": original["vendor_id"],
            "vendor_name": original["vendor_name"],
            "department": original["department"],
            "category": original["category"],
            # Amount nearly identical (small rounding-style difference) to simulate
            # a resubmitted or duplicated invoice rather than an exact copy-paste.
            "amount": round(original["amount"] * random.uniform(0.98, 1.02), 2),
            "payment_method": original["payment_method"],
            "invoice_id": f"INV-{next_id:05d}",  # different invoice number on purpose
            "description": original["description"],
            "approval_status": "Approved",
        }
        transactions.append(duplicate)
        log_anomaly(
            "duplicate_invoice",
            f"{original['transaction_id']} / {duplicate['transaction_id']}",
            f"Near-duplicate pair: same vendor ({original['vendor_id']}), same description, amounts within "
            f"2% of each other (₹{original['amount']} vs ₹{duplicate['amount']}), dated "
            f"{original['date']} and {dup_date} — different invoice numbers, so exact invoice-number "
            "matching would miss this; fuzzy/amount+vendor+date matching should catch it.",
        )
        next_id += 1
    return transactions


def inject_large_outliers(transactions: list[dict], vendors_df: pd.DataFrame, num: int = 6) -> list[dict]:
    """Push a handful of transactions to 3-5x their vendor's historical average."""
    candidates = random.sample(transactions, num)
    for txn in candidates:
        vendor_avg = vendors_df.loc[vendors_df["vendor_id"] == txn["vendor_id"], "average_transaction"].values[0]
        multiplier = random.uniform(3.2, 4.8)
        old_amount = txn["amount"]
        txn["amount"] = round(vendor_avg * multiplier, 2)
        log_anomaly(
            "amount_outlier",
            txn["transaction_id"],
            f"Amount inflated from ₹{old_amount} to ₹{txn['amount']} — {multiplier:.1f}x vendor "
            f"{txn['vendor_id']}'s historical average of ₹{vendor_avg}, simulating an unusually large charge.",
        )
    return transactions


def inject_repeated_payments(transactions: list[dict], num_clusters: int = 4) -> list[dict]:
    """Same vendor, same amount, paid multiple times within a short window —
    a classic accidental-double-payment or fraud pattern."""
    next_id = len(transactions) + 1
    for _ in range(num_clusters):
        original = random.choice(transactions)
        base_date = date.fromisoformat(original["date"])
        repeat_ids = []
        for offset in random.sample(range(1, 5), 2):  # 2 extra repeats within 4 days
            repeat_date = (base_date + timedelta(days=offset)).isoformat()
            repeat = {
                "transaction_id": f"TXN-{next_id:05d}",
                "date": repeat_date,
                "vendor_id": original["vendor_id"],
                "vendor_name": original["vendor_name"],
                "department": original["department"],
                "category": original["category"],
                "amount": original["amount"],  # identical amount
                "payment_method": original["payment_method"],
                "invoice_id": f"INV-{next_id:05d}",
                "description": original["description"],
                "approval_status": "Approved",
            }
            transactions.append(repeat)
            repeat_ids.append(repeat["transaction_id"])
            next_id += 1
        log_anomaly(
            "repeated_payment_frequency",
            f"{original['transaction_id']} + {', '.join(repeat_ids)}",
            f"Identical amount (₹{original['amount']}) paid to vendor {original['vendor_id']} three times "
            f"within a 4-day window ({original['date']} plus repeats) — unusual payment frequency signal.",
        )
    return transactions


# ---------------------------------------------------------------------------
# 3. BUDGETS
# ---------------------------------------------------------------------------

def generate_budgets(transactions_df: pd.DataFrame) -> pd.DataFrame:
    transactions_df = transactions_df.copy()
    transactions_df["month"] = pd.to_datetime(transactions_df["date"]).dt.strftime("%Y-%m")
    rows = []
    months = sorted(transactions_df["month"].unique())
    overrun_targets = set(random.sample([(d, m) for d in DEPARTMENTS for m in months], 5))

    for dept in DEPARTMENTS:
        for month in months:
            actual = transactions_df[(transactions_df["department"] == dept) & (transactions_df["month"] == month)]["amount"].sum()
            if (dept, month) in overrun_targets:
                # Set budget noticeably below actual to create a real overrun (20-40%)
                overrun_pct = random.uniform(0.20, 0.40)
                budget = round(actual / (1 + overrun_pct), 2)
                log_anomaly(
                    "budget_overrun",
                    f"{dept} / {month}",
                    f"Budget set to ₹{budget} against actual spending of ₹{round(actual, 2)} — "
                    f"a {overrun_pct*100:.0f}% overrun, simulating a department exceeding its allocation.",
                )
            else:
                # Budget comfortably above actual (10-30% headroom)
                headroom = random.uniform(0.10, 0.30)
                budget = round(actual * (1 + headroom), 2)
            rows.append({"department": dept, "month": month, "budget": budget, "actual_spending": round(actual, 2)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. RECEIVABLES
# ---------------------------------------------------------------------------

def generate_receivables(n: int = 120) -> pd.DataFrame:
    customers = [f"{prefix} {suffix}" for prefix in ["Orion", "Meridian", "Falcon", "Harborline", "Quantum", "Cedar", "Delta", "Ironclad"]
                 for suffix in ["Ltd", "Pvt Ltd", "Inc", "Corp"]]
    rows = []
    today = date(2025, 9, 1)  # analysis "as of" date, after the transaction window

    for i in range(1, n + 1):
        customer = random.choice(customers)
        invoice_date = random_date(date(2025, 5, 1), date(2025, 8, 25))
        due_date = invoice_date + timedelta(days=30)
        amount = round(np.random.lognormal(mean=9.5, sigma=0.9), 2)

        days_overdue = (today - due_date).days
        if days_overdue <= 0:
            status = "Paid" if random.random() < 0.7 else "Pending"
        else:
            status = random.choices(["Paid", "Overdue"], weights=[0.5, 0.5])[0]

        rows.append(
            {
                "invoice_id": f"REC-{i:05d}",
                "customer": customer,
                "invoice_date": invoice_date.isoformat(),
                "due_date": due_date.isoformat(),
                "amount": amount,
                "payment_status": status,
            }
        )

    df = pd.DataFrame(rows)

    # Force-inject a handful of clearly high-priority overdue invoices
    # (large amount, far past due) so the receivables monitor has obvious signal.
    high_priority_indices = random.sample(range(len(df)), 5)
    for idx in high_priority_indices:
        forced_due = today - timedelta(days=random.randint(45, 90))
        forced_invoice = forced_due - timedelta(days=30)
        df.loc[idx, "invoice_date"] = forced_invoice.isoformat()
        df.loc[idx, "due_date"] = forced_due.isoformat()
        df.loc[idx, "amount"] = round(random.uniform(150000, 350000), 2)
        df.loc[idx, "payment_status"] = "Overdue"
        log_anomaly(
            "high_priority_overdue_receivable",
            df.loc[idx, "invoice_id"],
            f"{df.loc[idx, 'customer']} — ₹{df.loc[idx, 'amount']:.0f}, "
            f"{(today - forced_due).days} days overdue — forced into the dataset as a high-value, "
            "high-priority overdue receivable.",
        )

    # Give 2 customers a repeated late-payment pattern (3+ overdue invoices each)
    repeat_late_customers = random.sample(customers, 2)
    for cust in repeat_late_customers:
        cust_indices = df[df["customer"] == cust].index[:3]
        for idx in cust_indices:
            forced_due = today - timedelta(days=random.randint(10, 40))
            df.loc[idx, "due_date"] = forced_due.isoformat()
            df.loc[idx, "payment_status"] = "Overdue"
        log_anomaly(
            "repeated_late_payer",
            cust,
            f"Customer given {len(cust_indices)} overdue invoices to simulate a repeated late-payment pattern.",
        )

    return df


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    vendors_df = generate_vendors(NUM_VENDORS)
    transactions = generate_base_transactions(vendors_df, NUM_BASE_TRANSACTIONS)
    transactions = inject_duplicate_invoices(transactions, num_pairs=8)
    transactions = inject_large_outliers(transactions, vendors_df, num=6)
    transactions = inject_repeated_payments(transactions, num_clusters=4)

    transactions_df = pd.DataFrame(transactions).sort_values("date").reset_index(drop=True)

    # Backfill vendor total_transactions / average_transaction from the actual generated data
    # so the vendors table is internally consistent with the transactions table.
    agg = transactions_df.groupby("vendor_id")["amount"].agg(["count", "mean"]).reset_index()
    agg.columns = ["vendor_id", "actual_total_transactions", "actual_average_transaction"]
    vendors_df = vendors_df.merge(agg, on="vendor_id", how="left")
    vendors_df["total_transactions"] = vendors_df["actual_total_transactions"].fillna(0).astype(int)
    vendors_df["average_transaction"] = vendors_df["actual_average_transaction"].fillna(vendors_df["average_transaction"]).round(2)
    vendors_df = vendors_df.drop(columns=["actual_total_transactions", "actual_average_transaction"])

    # Simple risk_level derived from vendor_age + txn volume (not from the anomalies
    # themselves) so it reads as a plausible pre-existing attribute, not a spoiler.
    def risk_from_profile(row):
        if row["vendor_age"] < 3:
            return "MEDIUM"
        if row["total_transactions"] > 25:
            return "LOW"
        return "LOW" if row["vendor_age"] > 12 else "MEDIUM"

    vendors_df["risk_level"] = vendors_df.apply(risk_from_profile, axis=1)

    budgets_df = generate_budgets(transactions_df)
    receivables_df = generate_receivables(120)

    vendors_df.to_csv(f"{OUTPUT_DIR}/vendors.csv", index=False)
    transactions_df.to_csv(f"{OUTPUT_DIR}/transactions.csv", index=False)
    budgets_df.to_csv(f"{OUTPUT_DIR}/budgets.csv", index=False)
    receivables_df.to_csv(f"{OUTPUT_DIR}/receivables.csv", index=False)

    write_manifest(vendors_df, transactions_df, budgets_df, receivables_df)

    print(f"vendors.csv: {len(vendors_df)} rows")
    print(f"transactions.csv: {len(transactions_df)} rows")
    print(f"budgets.csv: {len(budgets_df)} rows")
    print(f"receivables.csv: {len(receivables_df)} rows")
    print(f"anomalies_manifest.md: {len(manifest_entries)} documented anomalies")


def write_manifest(vendors_df, transactions_df, budgets_df, receivables_df):
    lines = [
        "# Synthetic Data Anomaly Manifest",
        "",
        f"Generated with random seed `{RANDOM_SEED}` — re-running `generate_synthetic_data.py` reproduces this exact dataset.",
        "",
        "This file documents every anomaly intentionally injected into the synthetic dataset.",
        "It exists for testing/grading detection accuracy in Phase 4/11 — **the detection code",
        "must never read this file**; it is ground truth for evaluating the detector, not an input to it.",
        "",
        f"- vendors.csv: {len(vendors_df)} rows",
        f"- transactions.csv: {len(transactions_df)} rows",
        f"- budgets.csv: {len(budgets_df)} rows",
        f"- receivables.csv: {len(receivables_df)} rows",
        "",
    ]

    by_category: dict[str, list[dict]] = {}
    for entry in manifest_entries:
        by_category.setdefault(entry["category"], []).append(entry)

    category_titles = {
        "duplicate_invoice": "## Duplicate Invoices",
        "amount_outlier": "## Amount Outliers (unusually large transactions)",
        "repeated_payment_frequency": "## Repeated Payments (same vendor/amount, short window)",
        "vendor_recently_created": "## Recently Created Vendors",
        "budget_overrun": "## Budget Overruns",
        "high_priority_overdue_receivable": "## High-Priority Overdue Receivables",
        "repeated_late_payer": "## Repeated Late-Paying Customers",
    }

    for category, title in category_titles.items():
        entries = by_category.get(category, [])
        if not entries:
            continue
        lines.append(title)
        lines.append("")
        for e in entries:
            lines.append(f"- **{e['record_id']}** — {e['reason']}")
        lines.append("")

    with open(f"{OUTPUT_DIR}/anomalies_manifest.md", "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
