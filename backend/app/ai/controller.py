"""
AI investigation controller.

Implements the workflow from the spec:
  User clicks "Investigate" -> Controller receives issue -> retrieves
  relevant data (via tools) -> collects evidence -> generates explanation
  -> generates recommendation -> presents evidence + recommendation.

Design choices worth being able to defend in an interview:
- Plain tool-calling loop, no LangGraph. At this scale (one investigation
  flow, no branching multi-agent behavior) a framework would add
  indirection without adding capability — LangGraph earns its keep when
  you have multiple interacting agents or complex state machines, which
  this genuinely isn't.
- Two-phase: (1) let the model call tools freely to gather evidence,
  (2) one final call with JSON-mode structured output, using only the
  gathered tool results as context. Forcing JSON mode *while* tools are
  still being called is unreliable across providers; separating the
  phases makes the final output format reliable without fighting the
  API.
- Hard iteration cap (MAX_TOOL_ITERATIONS) so a model that keeps calling
  tools indefinitely can't hang a request or blow through API costs.
- The model is explicitly told the risk score is authoritative (from
  calculate_risk) and it must not invent or override it — this mirrors
  the spec's "AI must not invent financial facts" requirement.
"""

import json

from groq import Groq
from sqlalchemy.orm import Session

from app.ai.tools import TOOL_FUNCTIONS, TOOL_SCHEMAS
from app.config import get_settings

MAX_TOOL_ITERATIONS = 6

SYSTEM_PROMPT = """You are FinGuard AI, an evidence-driven finance investigation assistant.

You are investigating a flagged financial anomaly. You have tools to retrieve real
data about the transaction, vendor, budgets, receivables, and cash flow. Use them
to gather evidence before drawing any conclusion.

Rules you must follow:
1. NEVER invent or guess a financial fact, amount, date, or score. Only state
   things you retrieved via a tool call.
2. The risk score from calculate_risk is authoritative - report it exactly,
   do not recalculate or override it yourself.
3. Call calculate_risk and get_transaction at minimum. Call other tools
   (get_vendor_history, find_similar_invoices, get_related_transactions, etc.)
   whenever they would strengthen or clarify the evidence.
4. If a tool returns an error or no data, say so explicitly rather than
   filling the gap with an assumption.
5. Do not autonomously approve, reject, or resolve anything - you only
   investigate and recommend. A human makes the final decision.
"""


def _get_client() -> Groq:
    settings = get_settings()
    return Groq(api_key=settings.groq_api_key)


def _execute_tool_call(db: Session, tool_call) -> dict:
    name = tool_call.function.name
    try:
        args = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        return {"error": f"Could not parse arguments for tool {name}"}

    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return {"error": f"Unknown tool: {name}"}

    try:
        return func(db, **args)
    except TypeError as e:
        return {"error": f"Invalid arguments for {name}: {e}"}


def investigate_anomaly(db: Session, anomaly_id: int) -> dict:
    """Runs the full tool-calling investigation loop and returns a dict with
    keys: evidence (list[str]), explanation (str), recommendation (str),
    risk_score (int), tool_calls_made (list[str] - for transparency/debugging)."""
    settings = get_settings()
    client = _get_client()

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Investigate anomaly ID {anomaly_id}. Start by calling calculate_risk "
                f"with this anomaly_id, then get_transaction for the flagged transaction, "
                f"then gather whatever additional evidence is relevant."
            ),
        },
    ]

    tool_calls_made = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
        message = response.choices[0].message

        if not message.tool_calls:
            break

        messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})

        for tool_call in message.tool_calls:
            result = _execute_tool_call(db, tool_call)
            tool_calls_made.append(f"{tool_call.function.name}({tool_call.function.arguments})")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, default=str),
                }
            )
    else:
        messages.append(
            {
                "role": "user",
                "content": "You've gathered enough evidence. Stop calling tools and produce your final structured answer now.",
            }
        )

    messages.append(
        {
            "role": "user",
            "content": (
                "Based only on the evidence gathered above, respond with a JSON object with exactly "
                "these keys: "
                '"risk_score" (integer, from calculate_risk\'s result - do not change it), '
                '"evidence" (array of short strings, each a concrete fact you retrieved), '
                '"explanation" (a few sentences on why this was flagged, referencing the evidence), '
                '"recommendation" (one sentence: what should the finance manager do - e.g. hold for '
                "manual verification, approve, escalate for review)."
            ),
        }
    )

    final_response = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        response_format={"type": "json_object"},
    )

    try:
        parsed = json.loads(final_response.choices[0].message.content)
    except (json.JSONDecodeError, TypeError):
        parsed = {
            "risk_score": 0,
            "evidence": ["AI response could not be parsed as structured JSON"],
            "explanation": final_response.choices[0].message.content or "No explanation generated.",
            "recommendation": "Manual review required - AI output was malformed.",
        }

    parsed["tool_calls_made"] = tool_calls_made
    return parsed
