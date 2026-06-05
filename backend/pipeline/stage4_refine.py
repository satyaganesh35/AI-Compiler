import json
import anthropic
from models import (
    DBSchema, APISchema, UISchema, AuthSchema,
    IntentSchema, ValidationIssue, DesignSchema
)
from .simulator import simulate_execution


def validate(
    intent: IntentSchema,
    db: DBSchema,
    api: APISchema,
    ui: UISchema,
    auth: AuthSchema,
    design: DesignSchema
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    db_table_names = {t.name for t in db.tables}
    db_columns: dict[str, set[str]] = {
        t.name: {c.name for c in t.columns} for t in db.tables
    }
    api_paths = {e.path for e in api.endpoints}
    intent_roles = set(intent.roles)

    # Rule 1: every API endpoint must reference a real DB table
    for ep in api.endpoints:
        if ep.db_table not in db_table_names:
            issues.append(ValidationIssue(
                layer="api→db",
                issue=f"Endpoint {ep.method} {ep.path} references unknown table '{ep.db_table}'",
                severity="error"
            ))

    # Rule 2: API request body fields must exist in the referenced DB table
    for ep in api.endpoints:
        if ep.db_table in db_columns:
            for field in ep.request_body:
                if field.name not in db_columns[ep.db_table] and field.name not in ("id", "created_at", "updated_at"):
                    issues.append(ValidationIssue(
                        layer="api→db",
                        issue=f"Endpoint {ep.path} request field '{field.name}' not in table '{ep.db_table}'",
                        severity="warning"
                    ))

    # Rule 3: UI components referencing unknown API endpoints
    for page in ui.pages:
        for comp in page.components:
            if comp.api_endpoint and comp.api_endpoint not in api_paths:
                issues.append(ValidationIssue(
                    layer="ui→api",
                    issue=f"Page '{page.name}' component '{comp.label}' references unknown endpoint '{comp.api_endpoint}'",
                    severity="error"
                ))

    # Rule 4: Roles in UI pages must exist in intent
    for page in ui.pages:
        for role in page.accessible_by:
            if role not in intent_roles:
                issues.append(ValidationIssue(
                    layer="ui→auth",
                    issue=f"Page '{page.name}' grants access to unknown role '{role}'",
                    severity="error"
                ))

    # Rule 5: Auth roles must match intent roles
    for rp in auth.role_permissions:
        if rp.role not in intent_roles:
            issues.append(ValidationIssue(
                layer="auth",
                issue=f"Auth schema defines unknown role '{rp.role}'",
                severity="warning"
            ))

    # Rule 6: All intent roles must have auth permissions
    auth_roles = {rp.role for rp in auth.role_permissions}
    for role in intent_roles:
        if role not in auth_roles:
            issues.append(ValidationIssue(
                layer="auth",
                issue=f"Intent role '{role}' has no auth permissions defined",
                severity="error"
            ))

    # Run the execution simulator checks
    sim_issues = simulate_execution(intent, db, api, ui, auth, design)
    issues.extend(sim_issues)

    return issues


REPAIR_SYSTEM = """You are the Repair Engine of an app-generation compiler.
You receive a JSON schema and a list of validation errors.
Fix ONLY the reported issues. Do not change anything else.
Output ONLY the corrected JSON. No markdown, no explanation, no backticks."""


import os

def repair_layer(
    client: anthropic.Anthropic,
    layer_name: str,
    layer_json: str,
    issues: list[ValidationIssue],
    context_json: str = ""
) -> str:
    issue_list = "\n".join(f"- [{i.severity}] {i.issue}" for i in issues)
    user_msg = f"""Fix these issues in the {layer_name} schema:

Issues to fix:
{issue_list}

{f'Context (other schemas for reference):{chr(10)}{context_json}' if context_json else ''}

{layer_name} schema to fix:
{layer_json}"""

    model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
    response = client.messages.create(
        model=model,
        max_tokens=2000,
        temperature=0.1,
        system=REPAIR_SYSTEM,
        messages=[{"role": "user", "content": user_msg}]
    )
    return response.content[0].text.strip()


def run(
    client: anthropic.Anthropic,
    intent: IntentSchema,
    db: DBSchema,
    api: APISchema,
    ui: UISchema,
    auth: AuthSchema,
    design: DesignSchema,
    max_repair_rounds: int = 2
) -> tuple[DBSchema, APISchema, UISchema, AuthSchema, list[ValidationIssue], int]:
    total_repairs = 0
    all_issues: list[ValidationIssue] = []

    for round_num in range(max_repair_rounds):
        issues = validate(intent, db, api, ui, auth, design)

        if not issues:
            break

        # Mark previous issues as seen
        all_issues.extend(issues)

        # Group by layer
        db_issues = [i for i in issues if "db" in i.layer and "api" not in i.layer]
        api_issues = [i for i in issues if "api" in i.layer]
        ui_issues = [i for i in issues if "ui" in i.layer]
        auth_issues = [i for i in issues if "auth" in i.layer and "ui" not in i.layer]

        context = f"DB schema:\n{db.model_dump_json()}\n\nAPI schema:\n{api.model_dump_json()}"

        if api_issues:
            fixed_json = repair_layer(client, "API", api.model_dump_json(indent=2), api_issues, context)
            try:
                api = APISchema(**json.loads(fixed_json))
                for i in api_issues:
                    i.auto_fixed = True
                total_repairs += len(api_issues)
            except Exception:
                pass  # keep original if repair produced invalid JSON

        if ui_issues:
            fixed_json = repair_layer(client, "UI", ui.model_dump_json(indent=2), ui_issues,
                                      f"API paths: {[e.path for e in api.endpoints]}\nRoles: {intent.roles}")
            try:
                ui = UISchema(**json.loads(fixed_json))
                for i in ui_issues:
                    i.auto_fixed = True
                total_repairs += len(ui_issues)
            except Exception:
                pass

        if auth_issues:
            fixed_json = repair_layer(client, "Auth", auth.model_dump_json(indent=2), auth_issues,
                                      f"Roles from intent: {intent.roles}")
            try:
                auth = AuthSchema(**json.loads(fixed_json))
                for i in auth_issues:
                    i.auto_fixed = True
                total_repairs += len(auth_issues)
            except Exception:
                pass

        if db_issues:
            fixed_json = repair_layer(client, "DB", db.model_dump_json(indent=2), db_issues)
            try:
                db = DBSchema(**json.loads(fixed_json))
                for i in db_issues:
                    i.auto_fixed = True
                total_repairs += len(db_issues)
            except Exception:
                pass

    return db, api, ui, auth, all_issues, total_repairs
