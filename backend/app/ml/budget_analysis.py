"""
Budget monitoring: compares budget vs actual spend per department/month
and classifies risk. Pure arithmetic, deliberately not ML — there's
nothing to learn here, just a calculation that needs to be transparent
and auditable (a finance manager needs to trust this number instantly).
"""

from dataclasses import dataclass

import pandas as pd

OVERRUN_HIGH_RISK_PCT = 15.0  # overrun >= this % is HIGH risk
OVERRUN_MEDIUM_RISK_PCT = 5.0  # overrun >= this % (but < HIGH) is MEDIUM risk


@dataclass
class BudgetStatus:
    department: str
    month: str
    budget: float
    actual_spending: float
    remaining_budget: float
    utilization_pct: float
    overrun_pct: float  # 0 if under budget
    risk_level: str  # LOW / MEDIUM / HIGH


def analyze_budgets(budgets_df: pd.DataFrame) -> list[BudgetStatus]:
    results = []
    for _, row in budgets_df.iterrows():
        budget = row["budget"]
        actual = row["actual_spending"]
        remaining = budget - actual
        utilization = round((actual / budget) * 100, 1) if budget else 0.0
        overrun = round(max(0.0, (actual - budget) / budget * 100), 1) if budget else 0.0

        if overrun >= OVERRUN_HIGH_RISK_PCT:
            risk = "HIGH"
        elif overrun >= OVERRUN_MEDIUM_RISK_PCT:
            risk = "MEDIUM"
        else:
            risk = "LOW"

        results.append(
            BudgetStatus(
                department=row["department"],
                month=row["month"],
                budget=budget,
                actual_spending=actual,
                remaining_budget=round(remaining, 2),
                utilization_pct=utilization,
                overrun_pct=overrun,
                risk_level=risk,
            )
        )
    return sorted(results, key=lambda b: b.overrun_pct, reverse=True)
