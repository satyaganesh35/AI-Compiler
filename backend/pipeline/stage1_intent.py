import json
import os
import anthropic
from models import IntentSchema

# ... SYSTEM_PROMPT matches previous code ...
SYSTEM_PROMPT = """You are the Intent Extraction stage of an app-generation compiler.
Your ONLY job is to parse a user's app description into a strict JSON object.

Rules:
- Output ONLY valid JSON. No markdown, no explanation, no backticks.
- If something is ambiguous, add it to the "ambiguities" list.
- If you assume something not stated, add it to the "assumptions" list.
- "entities" are the core data models (nouns), e.g. User, Contact, Invoice.
- "features" are functional capabilities, e.g. login, dashboard, export.
- "roles" are user types with different access levels.
- "constraints" are rules like "premium gating" or "read-only for guests".

Output this exact JSON shape:
{
  "app_name": "string",
  "app_type": "string",
  "entities": ["string"],
  "features": ["string"],
  "roles": ["string"],
  "constraints": ["string"],
  "ambiguities": ["string"],
  "assumptions": ["string"]
}"""


def run(client: anthropic.Anthropic, prompt: str) -> IntentSchema:
    model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0.2,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Extract intent from this app description:\n\n{prompt}"}]
    )
    raw = response.content[0].text.strip()
    data = json.loads(raw)
    return IntentSchema(**data)
