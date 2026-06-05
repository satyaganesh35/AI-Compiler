import json
import os
import anthropic
from models import IntentSchema, DesignSchema

SYSTEM_PROMPT = """You are the System Design stage of an app-generation compiler.
You receive structured intent JSON and output an app architecture blueprint.

Rules:
- Output ONLY valid JSON. No markdown, no explanation, no backticks.
- "entity_relations" must only reference entities present in the intent.
- "user_flows" must have one entry per role, describing their typical journey.
- "business_rules" are enforcement rules the app must implement.

Output this exact JSON shape:
{
  "architecture_type": "string",
  "auth_strategy": "string",
  "entity_relations": [
    {"from_entity": "string", "to_entity": "string", "relation": "string"}
  ],
  "user_flows": [
    {"role": "string", "flow": ["step1", "step2"]}
  ],
  "business_rules": ["string"]
}"""


def run(client: anthropic.Anthropic, intent: IntentSchema) -> DesignSchema:
    model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        temperature=0.2,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Generate the system design for this intent:\n\n{intent.model_dump_json(indent=2)}"
        }]
    )
    raw = response.content[0].text.strip()
    data = json.loads(raw)
    return DesignSchema(**data)
