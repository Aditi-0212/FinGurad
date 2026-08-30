"""
Cash-flow risk forecasting.

Deliberately simple per the spec: linear regression on daily net cash
position (inflows from receivables collections minus outflows from
transactions), projected forward to estimate when/if a deficit occurs.

Why linear regression over more complex forecasting (ARIMA, LSTM, etc.):
at a few months of daily data, a simple trend line is honest about its
own uncertainty and is trivial to explain to a finance manager: "spending
is outpacing income at roughly this rate, so at this rate we run out in
N days." A more sophisticated model would not meaningfully improve
accuracy on this little data and would be much harder to justify or
explain in a demo/interview. This is explicitly an estimate, not a fact,
and is presented as such.
"""

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

FORECAST_HORIZON_DAYS = 60
# Assumed starting cash reserve for demo purposes. Sized so the forecast reads
# realistically against this synthetic dataset's spending/collection scale
# (total transaction outflow considerably exceeds paid receivables in this
# sample data — a real deployment would pull this from actual bank/ledger
# balances instead of assuming it).
STARTING_CASH_ASSUMPTION = 3_000_000


@dataclass
class CashflowForecast:
    as_of_date: str
    current_cash_estimate: float
    daily_net_change_trend: float  # positive = growing, negative = shrinking
    projected_deficit_date: str | None  # None if no deficit projected within horizon
    days_until_deficit: int | None
    forecast_points: list[dict]  # [{date, projected_cash}, ...] for charting


def forecast_cashflow(transactions_df: pd.DataFrame, receivables_df: pd.DataFrame) -> CashflowForecast:
    tx = transactions_df.copy()
    tx["date"] = pd.to_datetime(tx["date"]).dt.date
    daily_outflow = tx.groupby("date")["amount"].sum()

    rec = receivables_df.copy()
    rec["due_date"] = pd.to_datetime(rec["due_date"]).dt.date
    paid = rec[rec["payment_status"] == "Paid"]
    daily_inflow = paid.groupby("due_date")["amount"].sum()

    all_dates = sorted(set(daily_outflow.index) | set(daily_inflow.index))
    if not all_dates:
        raise ValueError("No transaction or receivable dates available to forecast from")

    net_daily = pd.Series(
        [daily_inflow.get(d, 0) - daily_outflow.get(d, 0) for d in all_dates],
        index=all_dates,
    )

    # Running cash position starting from an assumed baseline.
    cumulative_cash = STARTING_CASH_ASSUMPTION + net_daily.cumsum()

    # Fit a simple linear trend to get the daily rate of change, but anchor
    # projections at the ACTUAL current cash position rather than the fitted
    # line's own value there — a regression fit to a noisy cumulative series
    # doesn't necessarily pass through the last real data point, and using
    # its raw value would silently shift the whole forecast by that residual.
    x = np.arange(len(cumulative_cash))
    y = cumulative_cash.values
    slope, _ = np.polyfit(x, y, 1)

    as_of = all_dates[-1]
    current_cash = float(cumulative_cash.iloc[-1])

    forecast_points = []
    deficit_date = None
    days_until_deficit = None

    for i in range(1, FORECAST_HORIZON_DAYS + 1):
        projected = current_cash + slope * i
        future_date = as_of + timedelta(days=i)
        forecast_points.append({"date": future_date.isoformat(), "projected_cash": round(projected, 2)})
        if projected < 0 and deficit_date is None:
            deficit_date = future_date
            days_until_deficit = i

    return CashflowForecast(
        as_of_date=as_of.isoformat(),
        current_cash_estimate=round(current_cash, 2),
        daily_net_change_trend=round(float(slope), 2),
        projected_deficit_date=deficit_date.isoformat() if deficit_date else None,
        days_until_deficit=days_until_deficit,
        forecast_points=forecast_points,
    )