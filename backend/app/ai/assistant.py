"""
AI Finance Assistant.

Same tool-calling architecture as the investigation controller (Phase 8),
reused deliberately rather than building a second bespoke loop — the
only real difference is the system prompt (open-ended Q&A vs a fixed
investigation workflow) and that this one returns free-text prose
instead of forcing JSON, since assistant answers are meant to be read
directly, not parsed by other code.

Per the spec: this must not become a generic ChatGPT wrapper. The system
prompt forces tool use for anything factual, and refuses to answer
from "knowledge" the model doesn't actually have tool-backed evidence for.
"""

import json

from groq import Groq
from sqlalchemy.orm import Session

from app.ai.tools import TOOL_FUNCTIONS, TOOL_SCHEMAS
from app.config import get_settings

MAX_TOOL_ITERATIONS = 6

ASSISTANT_SYSTEM_PROMPT = """You are the FinGuard AI Finance Assistant, answering a finance
manager's questions using the company's real financial data.

Rules:
1. Never answer a factual question (numbers, dates, names, amounts, risk scores) from
   your own assumptions. Always call the relevant tool first and base your answer only
   on what it returns.
2. If no tool can answer the question, say so plainly rather than guessing.
3. When you cite a number, be specific (e.g. "Marketing overran its June budget by 18%",
   not "some departments are over budget").
4. Keep answers concise and finance-manager-appropriate — a few sentences or a short
   list, not an essay.
5. You cannot approve, reject, or change any financial record — you only answer questions.
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


def ask_assistant(db: Session, question: str) -> dict:
    """Returns {"answer": str, "tool_calls_made": list[str]}."""
    settings = get_settings()
    client = _get_client()

    messages = [
        {"role": "system", "content": ASSISTANT_SYSTEM_PROMPT},
        {"role": "user", "content": question},
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
            return {"answer": message.content or "", "tool_calls_made": tool_calls_made}

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

    # Hit the iteration cap — force a final answer with what's been gathered.
    messages.append({"role": "user", "content": "Please answer now based on the data gathered so far."})
    final_response = client.chat.completions.create(model=settings.groq_model, messages=messages)
    return {
        "answer": final_response.choices[0].message.content or "",
        "tool_calls_made": tool_calls_made,
    }
