from models import DBSchema, APISchema, UISchema, AuthSchema, DesignSchema, ValidationIssue
from typing import Any, Optional

def simulate_execution(
    intent: Any,
    db: DBSchema,
    api: APISchema,
    ui: UISchema,
    auth: AuthSchema,
    design: DesignSchema
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    
    # 1. Build DB table lookups
    db_tables = {t.name: t for t in db.tables}
    
    # 2. Build API endpoint lookups
    # Map (method, path) -> endpoint
    api_endpoints = {}
    for ep in api.endpoints:
        api_endpoints[(ep.method.upper(), ep.path.strip())] = ep

    # 3. Build UI page lookups
    ui_pages_by_route = {p.route: p for p in ui.pages}
    ui_pages_by_name = {p.name.lower(): p for p in ui.pages}
    
    # 4. Build Role Permissions lookup
    # role -> resource -> set(actions)
    role_perms = {}
    for rp in auth.role_permissions:
        role_perms[rp.role] = {p.resource.lower(): set(p.actions) for p in rp.permissions}
        
    # Trace user flows
    for user_flow in design.user_flows:
        role = user_flow.role
        flow_steps = user_flow.flow
        
        # Track the simulated DB state for this flow to check inserts/updates
        # Table -> list of dicts (mock rows)
        mock_db: dict[str, list[dict[str, Any]]] = {t_name: [] for t_name in db_tables}
        
        # Check if this role is allowed in the auth schema
        if role not in auth.roles:
            issues.append(ValidationIssue(
                layer="runtime→auth",
                issue=f"User flow role '{role}' is not defined in AuthSchema roles",
                severity="error"
            ))
            continue
            
        for step_idx, step in enumerate(flow_steps):
            # Try to resolve what page this step corresponds to.
            # Simple keyword matching:
            step_words = set(step.lower().replace("-", " ").replace("_", " ").split())
            best_match = None
            max_intersection = 0
            
            for p_name, page in ui_pages_by_name.items():
                if role not in page.accessible_by:
                    continue
                name_words = set(p_name.split())
                intersection = len(step_words.intersection(name_words))
                if intersection > max_intersection:
                    max_intersection = intersection
                    best_match = page
            
            resolved_page = best_match
            if not resolved_page and len(ui.pages) > 0:
                # Fallback: if no page name matched, try to match by route keywords
                for page in ui.pages:
                    if role not in page.accessible_by:
                        continue
                    route_words = set(page.route.lower().replace("/", " ").split())
                    intersection = len(step_words.intersection(route_words))
                    if intersection > max_intersection:
                        max_intersection = intersection
                        resolved_page = page
            
            if not resolved_page and len(ui.pages) > 0:
                # Last resort fallback: check if there's any page at all
                resolved_page = ui.pages[0]
                
            if not resolved_page:
                issues.append(ValidationIssue(
                    layer="runtime→ui",
                    issue=f"Flow step '{step}' for role '{role}': no accessible UI page found in UISchema",
                    severity="warning"
                ))
                continue
                
            # Simulate navigation/actions on the resolved page
            # Look at page components to see if any matches the flow step
            matched_component = None
            max_comp_intersection = 0
            
            for comp in resolved_page.components:
                label_words = set(comp.label.lower().replace("-", " ").replace("_", " ").split())
                intersection = len(step_words.intersection(label_words))
                if intersection > max_comp_intersection:
                    max_comp_intersection = intersection
                    matched_component = comp
                    
            if not matched_component and len(resolved_page.components) > 0:
                matched_component = resolved_page.components[0]
                
            if not matched_component:
                continue
                
            # If the component calls an API endpoint, simulate the API call
            if matched_component.api_endpoint:
                api_path = matched_component.api_endpoint
                
                # Search api_endpoints for this path
                endpoint = None
                for (m, p), ep in api_endpoints.items():
                    if p == api_path:
                        endpoint = ep
                        break
                        
                if not endpoint:
                    issues.append(ValidationIssue(
                        layer="runtime→api",
                        issue=f"UI component '{matched_component.label}' on page '{resolved_page.name}' references API endpoint '{api_path}' which does not exist in API schema",
                        severity="error"
                    ))
                    continue
                    
                # 1. Access Control check: does the active role have access to this endpoint?
                if role not in endpoint.allowed_roles:
                    issues.append(ValidationIssue(
                        layer="runtime→auth",
                        issue=f"RBAC Violation: Role '{role}' in user flow '{step}' cannot call '{endpoint.method} {endpoint.path}'. Allowed roles: {endpoint.allowed_roles}",
                        severity="error"
                    ))
                    
                # 2. Database table verification
                db_table_name = endpoint.db_table
                if db_table_name not in db_tables:
                    issues.append(ValidationIssue(
                        layer="runtime→db",
                        issue=f"API endpoint '{endpoint.method} {endpoint.path}' references database table '{db_table_name}' which does not exist",
                        severity="error"
                    ))
                    continue
                    
                db_table = db_tables[db_table_name]
                table_cols = {c.name: c for c in db_table.columns}
                
                # 3. Simulate DB operations
                if endpoint.method.upper() in ("POST", "PUT"):
                    # Simulate Insert/Update
                    # Build mock request body:
                    mock_record = {}
                    for field in endpoint.request_body:
                        field_type = field.type.lower()
                        mock_val = None
                        if "int" in field_type:
                            mock_val = 1
                        elif "bool" in field_type:
                            mock_val = True
                        elif "date" in field_type:
                            mock_val = "2026-06-05T00:00:00"
                        else:
                            mock_val = "mock_string"
                        mock_record[field.name] = mock_val
                        
                    # Validate DB Schema rules against the request body fields
                    for col_name, col in table_cols.items():
                        if col.primary_key:
                            continue
                        if not col.nullable and col.default is None:
                            if col_name not in mock_record and col_name not in ("created_at", "updated_at"):
                                issues.append(ValidationIssue(
                                    layer="runtime→db",
                                    issue=f"Database constraint violation on '{db_table_name}': Non-nullable column '{col_name}' is missing from API request body of '{endpoint.method} {endpoint.path}'",
                                    severity="error"
                                ))
                                
                    mock_db[db_table_name].append(mock_record)
                    
                elif endpoint.method.upper() == "GET":
                    # Simulate SELECT
                    # Ensure database columns match the response fields expected
                    for field in endpoint.response_fields:
                        if field.name not in table_cols and field.name not in ("id", "created_at", "updated_at"):
                            issues.append(ValidationIssue(
                                layer="runtime→db",
                                issue=f"API response field '{field.name}' in endpoint '{endpoint.path}' does not map to any column in DB table '{db_table_name}'",
                                severity="warning"
                            ))
                            
    return issues
