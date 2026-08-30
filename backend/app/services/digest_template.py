"""
Renders DigestData into an email-safe HTML string.

Inline styles only — no <style> block, no external CSS, no flexbox/grid.
Email clients (Outlook especially) strip or mis-render anything fancier
than tables and inline styles, so this deliberately doesn't reuse the
frontend's Tailwind approach at all.
"""

from app.services.digest_service import DigestData

BG = "#0B0F14"
SURFACE = "#131920"
BORDER = "#232C36"
INK = "#E6EAEE"
MUTED = "#8B96A3"
ACCENT = "#2DD4BF"
RISK_HIGH = "#F87171"
RISK_MED = "#F59E0B"


def _risk_color(score: int) -> str:
    if score >= 70:
        return RISK_HIGH
    if score >= 40:
        return RISK_MED
    return "#34D399"


def render_digest_html(data: DigestData) -> str:
    health_color = "#34D399" if data.health_score >= 70 else RISK_MED if data.health_score >= 40 else RISK_HIGH

    anomaly_rows = "".join(
        f"""<tr>
              <td style="padding:8px 0;color:{INK};font-family:monospace;font-size:13px;">{a['transaction_id']}</td>
              <td style="padding:8px 0;color:{MUTED};font-size:13px;">{'Duplicate Invoice' if a['type']=='duplicate_invoice' else 'Anomaly'}</td>
              <td style="padding:8px 0;text-align:right;color:{_risk_color(a['risk_score'])};font-family:monospace;font-size:13px;font-weight:600;">{a['risk_score']}/100</td>
            </tr>"""
        for a in data.high_risk_anomalies
    ) or f'<tr><td style="padding:8px 0;color:{MUTED};font-size:13px;">No open high-risk alerts.</td></tr>'

    overrun_rows = "".join(
        f"""<tr>
              <td style="padding:8px 0;color:{INK};font-size:13px;">{b['department']} ({b['month']})</td>
              <td style="padding:8px 0;text-align:right;color:{RISK_HIGH};font-family:monospace;font-size:13px;font-weight:600;">+{b['overrun_pct']}%</td>
            </tr>"""
        for b in data.budget_overruns
    ) or f'<tr><td style="padding:8px 0;color:{MUTED};font-size:13px;">No budget overruns.</td></tr>'

    receivable_rows = "".join(
        f"""<tr>
              <td style="padding:8px 0;color:{INK};font-size:13px;">{r['customer']}</td>
              <td style="padding:8px 0;text-align:right;color:{MUTED};font-family:monospace;font-size:13px;">₹{r['amount']:,.0f}</td>
              <td style="padding:8px 0;text-align:right;color:{RISK_MED};font-family:monospace;font-size:13px;">{r['days_overdue']}d</td>
            </tr>"""
        for r in data.high_priority_receivables
    ) or f'<tr><td style="padding:8px 0;color:{MUTED};font-size:13px;">No high-priority overdue receivables.</td></tr>'

    cashflow_line = (
        f"Deficit projected in {data.cashflow_days_until_deficit} days"
        if data.cashflow_days_until_deficit is not None
        else "No deficit currently projected"
    )
    cashflow_color = RISK_HIGH if (data.cashflow_days_until_deficit or 999) < 30 else "#34D399"

    return f"""<html>
<head>
  <meta charset="utf-8">
</head>
<body style="margin:0;padding:0;background-color:{BG};font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:{BG};padding:24px 0;">
    <tr>
      <td align="center">
        <table width="560" cellpadding="0" cellspacing="0" style="background-color:{SURFACE};border:1px solid {BORDER};border-radius:8px;overflow:hidden;">
          <tr>
            <td style="padding:24px 28px;border-bottom:1px solid {BORDER};">
              <span style="color:{ACCENT};font-weight:700;font-size:14px;letter-spacing:0.5px;">FINGUARD AI</span>
              <div style="color:{MUTED};font-size:12px;margin-top:4px;">Daily Finance Digest — {data.generated_at}</div>
            </td>
          </tr>

          <tr>
            <td style="padding:24px 28px;border-bottom:1px solid {BORDER};">
              <div style="color:{MUTED};font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">Financial Health</div>
              <div style="font-family:monospace;font-size:32px;font-weight:700;color:{health_color};margin-top:4px;">{data.health_score}/100</div>
              <div style="color:{MUTED};font-size:12px;margin-top:4px;">
                Budget {data.health_breakdown.get('budget_health','-')} · Receivables {data.health_breakdown.get('receivables_health','-')} ·
                Cash Flow {data.health_breakdown.get('cashflow_health','-')} · Risk {data.health_breakdown.get('transaction_risk_health','-')}
              </div>
            </td>
          </tr>

          <tr>
            <td style="padding:24px 28px;border-bottom:1px solid {BORDER};">
              <div style="color:{INK};font-size:14px;font-weight:600;margin-bottom:2px;">Top Risk Alerts ({data.open_anomaly_count} open)</div>
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px;">
                {anomaly_rows}
              </table>
            </td>
          </tr>

          <tr>
            <td style="padding:24px 28px;border-bottom:1px solid {BORDER};">
              <div style="color:{INK};font-size:14px;font-weight:600;margin-bottom:2px;">Budget Overruns</div>
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px;">
                {overrun_rows}
              </table>
            </td>
          </tr>

          <tr>
            <td style="padding:24px 28px;border-bottom:1px solid {BORDER};">
              <div style="color:{INK};font-size:14px;font-weight:600;margin-bottom:2px;">High-Priority Overdue Receivables</div>
              <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px;">
                {receivable_rows}
              </table>
            </td>
          </tr>

          <tr>
            <td style="padding:24px 28px;">
              <div style="color:{INK};font-size:14px;font-weight:600;">Cash Position</div>
              <div style="font-family:monospace;font-size:20px;color:{INK};margin-top:6px;">₹{data.cashflow_current:,.0f}</div>
              <div style="color:{cashflow_color};font-size:13px;margin-top:2px;">{cashflow_line}</div>
            </td>
          </tr>

          <tr>
            <td style="padding:16px 28px;background-color:{BG};">
              <span style="color:{MUTED};font-size:11px;">Synthetic demo data — not real financial records.</span>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
