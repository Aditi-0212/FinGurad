# Synthetic Data Anomaly Manifest

Generated with random seed `42` — re-running `generate_synthetic_data.py` reproduces this exact dataset.

This file documents every anomaly intentionally injected into the synthetic dataset.
It exists for testing/grading detection accuracy in Phase 4/11 — **the detection code
must never read this file**; it is ground truth for evaluating the detector, not an input to it.

- vendors.csv: 45 rows
- transactions.csv: 666 rows
- budgets.csv: 36 rows
- receivables.csv: 120 rows

## Duplicate Invoices

- **TXN-00587 / TXN-00651** — Near-duplicate pair: same vendor (VEND-0028), same description, amounts within 2% of each other (₹4535.84 vs ₹4599.48), dated 2025-04-12 and 2025-04-14 — different invoice numbers, so exact invoice-number matching would miss this; fuzzy/amount+vendor+date matching should catch it.
- **TXN-00582 / TXN-00652** — Near-duplicate pair: same vendor (VEND-0033), same description, amounts within 2% of each other (₹5178.94 vs ₹5113.08), dated 2025-05-19 and 2025-05-20 — different invoice numbers, so exact invoice-number matching would miss this; fuzzy/amount+vendor+date matching should catch it.
- **TXN-00326 / TXN-00653** — Near-duplicate pair: same vendor (VEND-0023), same description, amounts within 2% of each other (₹4667.75 vs ₹4615.64), dated 2025-07-13 and 2025-07-16 — different invoice numbers, so exact invoice-number matching would miss this; fuzzy/amount+vendor+date matching should catch it.
- **TXN-00580 / TXN-00654** — Near-duplicate pair: same vendor (VEND-0006), same description, amounts within 2% of each other (₹4739.17 vs ₹4821.95), dated 2025-05-11 and 2025-05-12 — different invoice numbers, so exact invoice-number matching would miss this; fuzzy/amount+vendor+date matching should catch it.
- **TXN-00145 / TXN-00655** — Near-duplicate pair: same vendor (VEND-0030), same description, amounts within 2% of each other (₹5355.42 vs ₹5407.98), dated 2025-03-24 and 2025-03-26 — different invoice numbers, so exact invoice-number matching would miss this; fuzzy/amount+vendor+date matching should catch it.
- **TXN-00244 / TXN-00656** — Near-duplicate pair: same vendor (VEND-0025), same description, amounts within 2% of each other (₹2919.22 vs ₹2975.55), dated 2025-04-26 and 2025-04-28 — different invoice numbers, so exact invoice-number matching would miss this; fuzzy/amount+vendor+date matching should catch it.
- **TXN-00172 / TXN-00657** — Near-duplicate pair: same vendor (VEND-0024), same description, amounts within 2% of each other (₹1849.74 vs ₹1878.25), dated 2025-04-20 and 2025-04-23 — different invoice numbers, so exact invoice-number matching would miss this; fuzzy/amount+vendor+date matching should catch it.
- **TXN-00091 / TXN-00658** — Near-duplicate pair: same vendor (VEND-0028), same description, amounts within 2% of each other (₹6557.95 vs ₹6602.55), dated 2025-03-20 and 2025-03-23 — different invoice numbers, so exact invoice-number matching would miss this; fuzzy/amount+vendor+date matching should catch it.

## Amount Outliers (unusually large transactions)

- **TXN-00344** — Amount inflated from ₹3929.23 to ₹18960.52 — 4.3x vendor VEND-0002's historical average of ₹4400.13, simulating an unusually large charge.
- **TXN-00458** — Amount inflated from ₹1844.78 to ₹7930.37 — 3.8x vendor VEND-0034's historical average of ₹2108.71, simulating an unusually large charge.
- **TXN-00012** — Amount inflated from ₹7054.03 to ₹25901.81 — 4.5x vendor VEND-0037's historical average of ₹5808.58, simulating an unusually large charge.
- **TXN-00272** — Amount inflated from ₹7864.08 to ₹27506.73 — 4.4x vendor VEND-0018's historical average of ₹6319.52, simulating an unusually large charge.
- **TXN-00215** — Amount inflated from ₹24418.25 to ₹56971.7 — 3.3x vendor VEND-0007's historical average of ₹17385.13, simulating an unusually large charge.
- **TXN-00256** — Amount inflated from ₹7209.27 to ₹35426.64 — 3.9x vendor VEND-0008's historical average of ₹9081.07, simulating an unusually large charge.

## Repeated Payments (same vendor/amount, short window)

- **TXN-00430 + TXN-00659, TXN-00660** — Identical amount (₹3827.77) paid to vendor VEND-0029 three times within a 4-day window (2025-08-12 plus repeats) — unusual payment frequency signal.
- **TXN-00505 + TXN-00661, TXN-00662** — Identical amount (₹5025.11) paid to vendor VEND-0023 three times within a 4-day window (2025-05-24 plus repeats) — unusual payment frequency signal.
- **TXN-00560 + TXN-00663, TXN-00664** — Identical amount (₹2128.14) paid to vendor VEND-0017 three times within a 4-day window (2025-07-11 plus repeats) — unusual payment frequency signal.
- **TXN-00491 + TXN-00665, TXN-00666** — Identical amount (₹2780.35) paid to vendor VEND-0009 three times within a 4-day window (2025-05-24 plus repeats) — unusual payment frequency signal.

## Recently Created Vendors

- **VEND-0035** — Vendor age set to 2 months to simulate a newly onboarded vendor with limited transaction history — a common fraud/error risk signal.
- **VEND-0045** — Vendor age set to 1 months to simulate a newly onboarded vendor with limited transaction history — a common fraud/error risk signal.
- **VEND-0013** — Vendor age set to 1 months to simulate a newly onboarded vendor with limited transaction history — a common fraud/error risk signal.

## Budget Overruns

- **Marketing / 2025-04** — Budget set to ₹86529.64 against actual spending of ₹120304.97 — a 39% overrun, simulating a department exceeding its allocation.
- **Marketing / 2025-05** — Budget set to ₹80380.83 against actual spending of ₹97649.86 — a 21% overrun, simulating a department exceeding its allocation.
- **Marketing / 2025-07** — Budget set to ₹106171.22 against actual spending of ₹135378.03 — a 28% overrun, simulating a department exceeding its allocation.
- **Sales / 2025-03** — Budget set to ₹73180.64 against actual spending of ₹90825.23 — a 24% overrun, simulating a department exceeding its allocation.
- **HR / 2025-07** — Budget set to ₹61645.19 against actual spending of ₹84328.82 — a 37% overrun, simulating a department exceeding its allocation.

## High-Priority Overdue Receivables

- **REC-00022** — Delta Corp — ₹241185, 63 days overdue — forced into the dataset as a high-value, high-priority overdue receivable.
- **REC-00009** — Quantum Ltd — ₹269274, 78 days overdue — forced into the dataset as a high-value, high-priority overdue receivable.
- **REC-00106** — Falcon Corp — ₹236733, 66 days overdue — forced into the dataset as a high-value, high-priority overdue receivable.
- **REC-00006** — Delta Ltd — ₹349094, 88 days overdue — forced into the dataset as a high-value, high-priority overdue receivable.
- **REC-00039** — Ironclad Inc — ₹349228, 66 days overdue — forced into the dataset as a high-value, high-priority overdue receivable.

## Repeated Late-Paying Customers

- **Ironclad Corp** — Customer given 3 overdue invoices to simulate a repeated late-payment pattern.
- **Cedar Inc** — Customer given 3 overdue invoices to simulate a repeated late-payment pattern.
