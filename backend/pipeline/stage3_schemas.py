import json
import anthropic
from models import IntentSchema, DesignSchema, DBSchema, APISchema, UISchema, AuthSchema

# ── DB Schema ────────────────────────────────────────────────────────────────

DB_SYSTEM = """You are the Database Schema generator of an app-generation compiler.
Output ONLY valid JSON. No markdown, no backticks, no explanation.

Generate a complete relational DB schema. Each table must have:
- An "id" primary key column (INTEGER, primary_key: true)
- "created_at" timestamp column
- All columns needed for the entities and features

Output this exact shape:
{
  "tables": [
    {
      "name": "string",
      "columns": [
        {
          "name": "string",
          "type": "string",
          "nullable": false,
          "primary_key": false,
          "foreign_key": null,
          "unique": false,
          "default": null
        }
      ]
    }
  ]
}"""

API_SYSTEM = """You are the API Schema generator of an app-generation compiler.
Output ONLY valid JSON. No markdown, no backticks, no explanation.

Generate a complete REST API schema. Rules:
- Every CRUD operation needed for each entity must be covered.
- "db_table" must exactly match a table name from the DB schema provided.
- "allowed_roles" must only use roles from the intent.
- "request_body" and "response_fields" must map to actual DB columns.

Output this exact shape:
{
  "base_url": "/api",
  "endpoints": [
    {
      "path": "string",
      "method": "string",
      "description": "string",
      "auth_required": true,
      "allowed_roles": ["string"],
      "request_body": [{"name": "string", "type": "string", "required": true}],
      "response_fields": [{"name": "string", "type": "string", "required": true}],
      "db_table": "string"
    }
  ]
}"""

UI_SYSTEM = """You are the UI Schema generator of an app-generation compiler.
Output ONLY valid JSON. No markdown, no backticks, no explanation.

Generate a complete UI page/component schema. Rules:
- Every role must have at least one accessible page.
- "api_endpoint" in components must match an endpoint path from the API schema.
- Form fields must map to API request_body fields.

Output this exact shape:
{
  "pages": [
    {
      "name": "string",
      "route": "string",
      "accessible_by": ["string"],
      "components": [
        {
          "type": "string",
          "label": "string",
          "fields": ["string"],
          "api_endpoint": "string"
        }
      ]
    }
  ],
  "navigation": ["string"]
}"""

AUTH_SYSTEM = """You are the Auth Schema generator of an app-generation compiler.
Output ONLY valid JSON. No markdown, no backticks, no explanation.

Generate a complete auth and permissions schema. Rules:
- Every role from the intent must appear.
- Permissions must reference real entities/resources from the intent.
- Actions are one of: "read", "write", "update", "delete", "manage".

Output this exact shape:
{
  "strategy": "string",
  "roles": ["string"],
  "role_permissions": [
    {
      "role": "string",
      "permissions": [
        {"resource": "string", "actions": ["string"]}
      ]
    }
  ],
  "premium_features": ["string"]
}"""


import os

def _call(client: anthropic.Anthropic, system: str, user_msg: str) -> dict:
    model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    response = client.messages.create(
        model=model,
        max_tokens=2000,
        temperature=0.2,
        system=system,
        messages=[{"role": "user", "content": user_msg}]
    )
    return json.loads(response.content[0].text.strip())


def run(
    client: anthropic.Anthropic,
    intent: IntentSchema,
    design: DesignSchema
) -> tuple[DBSchema, APISchema, UISchema, AuthSchema]:
    context = f"Intent:\n{intent.model_dump_json(indent=2)}\n\nDesign:\n{design.model_dump_json(indent=2)}"

    db_data = _call(client, DB_SYSTEM, f"Generate DB schema for:\n\n{context}")
    db = DBSchema(**db_data)

    api_data = _call(client, API_SYSTEM,
        f"Generate API schema for:\n\n{context}\n\nDB Schema:\n{db.model_dump_json(indent=2)}")
    api = APISchema(**api_data)

    ui_data = _call(client, UI_SYSTEM,
        f"Generate UI schema for:\n\n{context}\n\nAPI Schema:\n{api.model_dump_json(indent=2)}")
    ui = UISchema(**ui_data)

    auth_data = _call(client, AUTH_SYSTEM, f"Generate auth schema for:\n\n{context}")
    auth = AuthSchema(**auth_data)

    return db, api, ui, auth
