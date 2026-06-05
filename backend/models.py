from pydantic import BaseModel, Field
from typing import Any, Optional


# ── Stage 1: Intent ──────────────────────────────────────────────────────────

class IntentSchema(BaseModel):
    app_name: str
    app_type: str                        # e.g. "CRM", "E-commerce", "Blog"
    entities: list[str]                  # e.g. ["User", "Contact", "Payment"]
    features: list[str]                  # e.g. ["login", "dashboard", "payments"]
    roles: list[str]                     # e.g. ["admin", "user", "premium"]
    constraints: list[str]               # e.g. ["premium gating", "role-based access"]
    ambiguities: list[str]               # e.g. ["what does premium include?"]
    assumptions: list[str]               # e.g. ["Stripe for payments assumed"]


# ── Stage 2: Design ──────────────────────────────────────────────────────────

class EntityRelation(BaseModel):
    from_entity: str
    to_entity: str
    relation: str                        # e.g. "has_many", "belongs_to"

class UserFlow(BaseModel):
    role: str
    flow: list[str]                      # ordered steps

class DesignSchema(BaseModel):
    architecture_type: str               # e.g. "REST", "monolith"
    auth_strategy: str                   # e.g. "JWT", "session"
    entity_relations: list[EntityRelation]
    user_flows: list[UserFlow]
    business_rules: list[str]


# ── Stage 3: DB Schema ───────────────────────────────────────────────────────

class DBColumn(BaseModel):
    name: str
    type: str                            # e.g. "VARCHAR(255)", "INTEGER", "BOOLEAN"
    nullable: bool = False
    primary_key: bool = False
    foreign_key: Optional[str] = None   # e.g. "users.id"
    unique: bool = False
    default: Optional[str] = None

class DBTable(BaseModel):
    name: str
    columns: list[DBColumn]

class DBSchema(BaseModel):
    tables: list[DBTable]


# ── Stage 3: API Schema ──────────────────────────────────────────────────────

class APIField(BaseModel):
    name: str
    type: str
    required: bool = True

class APIEndpoint(BaseModel):
    path: str                            # e.g. "/api/contacts"
    method: str                          # GET, POST, PUT, DELETE
    description: str
    auth_required: bool = True
    allowed_roles: list[str]
    request_body: list[APIField] = []
    response_fields: list[APIField] = []
    db_table: str                        # which DB table this touches

class APISchema(BaseModel):
    base_url: str = "/api"
    endpoints: list[APIEndpoint]


# ── Stage 3: UI Schema ───────────────────────────────────────────────────────

class UIComponent(BaseModel):
    type: str                            # e.g. "form", "table", "chart", "card"
    label: str
    fields: list[str] = []              # form field names
    api_endpoint: str = ""              # which endpoint it calls

class UIPage(BaseModel):
    name: str
    route: str
    accessible_by: list[str]            # roles
    components: list[UIComponent]

class UISchema(BaseModel):
    pages: list[UIPage]
    navigation: list[str]               # ordered page names in nav


# ── Stage 3: Auth Schema ─────────────────────────────────────────────────────

class Permission(BaseModel):
    resource: str
    actions: list[str]                  # e.g. ["read", "write", "delete"]

class RolePermission(BaseModel):
    role: str
    permissions: list[Permission]

class AuthSchema(BaseModel):
    strategy: str
    roles: list[str]
    role_permissions: list[RolePermission]
    premium_features: list[str] = []


# ── Stage 4: Final App Config ────────────────────────────────────────────────

class ValidationIssue(BaseModel):
    layer: str
    issue: str
    severity: str                        # "error" | "warning"
    auto_fixed: bool = False

class AppConfig(BaseModel):
    intent: IntentSchema
    design: DesignSchema
    db_schema: DBSchema
    api_schema: APISchema
    ui_schema: UISchema
    auth_schema: AuthSchema
    validation_issues: list[ValidationIssue] = []
    assumptions: list[str] = []
    retries: int = 0
    repairs: int = 0


# ── API Request/Response ─────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    prompt: str

class GenerateResponse(BaseModel):
    success: bool
    config: Optional[AppConfig] = None
    error: Optional[str] = None
    latency_ms: int = 0
    stage_latencies: dict[str, int] = {}
