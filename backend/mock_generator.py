import re
from models import (
    IntentSchema, DesignSchema, EntityRelation, UserFlow,
    DBSchema, DBTable, DBColumn,
    APISchema, APIEndpoint, APIField,
    UISchema, UIPage, UIComponent,
    AuthSchema, RolePermission, Permission,
    AppConfig, ValidationIssue
)

def generate_mock_config(prompt: str) -> AppConfig:
    prompt_lower = prompt.lower()
    
    # 1. Determine app category and parameters
    if "crm" in prompt_lower:
        app_name = "CRM System"
        app_type = "CRM"
        entities = ["User", "Contact", "Deals", "Payment"]
        features = ["login", "contacts", "dashboard", "payments", "analytics", "role-based access"]
        roles = ["Admin", "Manager", "User"]
        constraints = ["role-based access", "premium plan gating"]
        assumptions = ["Stripe payment gateway integrated", "JWT tokens for session security"]
        ambiguities = ["Should manager roles have transaction editing rights?"]
        
        # DB Table structures
        tables = [
            DBTable(name="users", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="username", type="VARCHAR(255)", nullable=False),
                DBColumn(name="email", type="VARCHAR(255)", nullable=False, unique=True),
                DBColumn(name="role", type="VARCHAR(50)", nullable=False),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ]),
            DBTable(name="contacts", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="first_name", type="VARCHAR(100)", nullable=False),
                DBColumn(name="last_name", type="VARCHAR(100)", nullable=False),
                DBColumn(name="email", type="VARCHAR(255)", nullable=False),
                DBColumn(name="phone", type="VARCHAR(50)", nullable=True),
                DBColumn(name="assigned_user_id", type="INTEGER", nullable=False, foreign_key="users.id"),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ]),
            DBTable(name="deals", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="name", type="VARCHAR(255)", nullable=False),
                DBColumn(name="value", type="DECIMAL(10,2)", nullable=False),
                DBColumn(name="stage", type="VARCHAR(50)", nullable=False),
                DBColumn(name="contact_id", type="INTEGER", nullable=False, foreign_key="contacts.id"),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ]),
            DBTable(name="payments", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="user_id", type="INTEGER", nullable=False, foreign_key="users.id"),
                DBColumn(name="amount", type="DECIMAL(10,2)", nullable=False),
                DBColumn(name="status", type="VARCHAR(50)", nullable=False),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ])
        ]
        
        # API Endpoints
        endpoints = [
            APIEndpoint(path="/api/users", method="GET", description="Get list of system users", allowed_roles=["Admin", "Manager"], db_table="users",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="username", type="string"), APIField(name="email", type="string"), APIField(name="role", type="string")]),
            APIEndpoint(path="/api/users", method="POST", description="Create system user", allowed_roles=["Admin"], db_table="users",
                        request_body=[APIField(name="username", type="string"), APIField(name="email", type="string"), APIField(name="role", type="string")]),
            APIEndpoint(path="/api/contacts", method="GET", description="Get user contacts list", allowed_roles=["Admin", "Manager", "User"], db_table="contacts",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="first_name", type="string"), APIField(name="last_name", type="string"), APIField(name="email", type="string"), APIField(name="phone", type="string"), APIField(name="assigned_user_id", type="integer")]),
            APIEndpoint(path="/api/contacts", method="POST", description="Add new contact details", allowed_roles=["Admin", "Manager", "User"], db_table="contacts",
                        request_body=[APIField(name="first_name", type="string"), APIField(name="last_name", type="string"), APIField(name="email", type="string"), APIField(name="assigned_user_id", type="integer")],
                        response_fields=[APIField(name="id", type="integer")]),
            APIEndpoint(path="/api/deals", method="GET", description="Retrieve pipeline deals", allowed_roles=["Admin", "Manager", "User"], db_table="deals",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="name", type="string"), APIField(name="value", type="number"), APIField(name="stage", type="string"), APIField(name="contact_id", type="integer")]),
            APIEndpoint(path="/api/deals", method="POST", description="Add pipeline deal", allowed_roles=["Admin", "Manager", "User"], db_table="deals",
                        request_body=[APIField(name="name", type="string"), APIField(name="value", type="number"), APIField(name="stage", type="string"), APIField(name="contact_id", type="integer")]),
            APIEndpoint(path="/api/payments", method="GET", description="Retrieve payment records", allowed_roles=["Admin", "Manager"], db_table="payments",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="user_id", type="integer"), APIField(name="amount", type="number"), APIField(name="status", type="string")]),
            APIEndpoint(path="/api/payments", method="POST", description="Process transaction details", allowed_roles=["Admin", "Manager", "User"], db_table="payments",
                        request_body=[APIField(name="user_id", type="integer"), APIField(name="amount", type="number"), APIField(name="status", type="string")])
        ]
        
        # UI Pages
        pages = [
            UIPage(name="Dashboard", route="/dashboard", accessible_by=["Admin", "Manager", "User"], components=[
                UIComponent(type="card", label="Welcome to CRM Dashboard"),
                UIComponent(type="table", label="Contact List Summary", api_endpoint="/api/contacts")
            ]),
            UIPage(name="Contacts", route="/contacts", accessible_by=["Admin", "Manager", "User"], components=[
                UIComponent(type="table", label="Manage CRM Contacts", api_endpoint="/api/contacts"),
                UIComponent(type="form", label="Add New Contact Details", api_endpoint="/api/contacts", fields=["first_name", "last_name", "email", "assigned_user_id"])
            ]),
            UIPage(name="Deals", route="/deals", accessible_by=["Admin", "Manager", "User"], components=[
                UIComponent(type="table", label="Sales deals pipeline list", api_endpoint="/api/deals"),
                UIComponent(type="form", label="Create New Deal", api_endpoint="/api/deals", fields=["name", "value", "stage", "contact_id"])
            ]),
            UIPage(name="Payments", route="/payments", accessible_by=["Admin", "Manager", "User"], components=[
                UIComponent(type="table", label="System transaction ledger", api_endpoint="/api/payments"),
                UIComponent(type="form", label="Process payments subscription", api_endpoint="/api/payments", fields=["user_id", "amount", "status"])
            ]),
            UIPage(name="Users", route="/users", accessible_by=["Admin", "Manager"], components=[
                UIComponent(type="table", label="System user list", api_endpoint="/api/users"),
                UIComponent(type="form", label="Invite new workspace user", api_endpoint="/api/users", fields=["username", "email", "role"])
            ]),
            UIPage(name="Analytics", route="/analytics", accessible_by=["Admin"], components=[
                UIComponent(type="chart", label="CRM Analytics details dashboard", api_endpoint="/api/deals")
            ])
        ]
        nav = ["Dashboard", "Contacts", "Deals", "Payments", "Users", "Analytics"]
        
        # Relations
        relations = [
            EntityRelation(from_entity="contacts", to_entity="users", relation="belongs_to"),
            EntityRelation(from_entity="deals", to_entity="contacts", relation="belongs_to"),
            EntityRelation(from_entity="payments", to_entity="users", relation="belongs_to")
        ]
        
        # Flows
        flows = [
            UserFlow(role="Admin", flow=["Dashboard", "Analytics", "Users", "Invite new workspace user"]),
            UserFlow(role="Manager", flow=["Dashboard", "Contacts", "Add New Contact Details", "Deals", "Create New Deal"]),
            UserFlow(role="User", flow=["Dashboard", "Contacts", "Deals"])
        ]
        rules = [
            "Only Admin users can view the Analytics page.",
            "Only Admin and Manager roles can view system user list.",
            "Managers can add contacts and create deals."
        ]
        
        # Auth
        role_permissions = [
            RolePermission(role="Admin", permissions=[
                Permission(resource="users", actions=["read", "write", "update", "delete"]),
                Permission(resource="contacts", actions=["read", "write", "update", "delete"]),
                Permission(resource="deals", actions=["read", "write", "update", "delete"]),
                Permission(resource="payments", actions=["read", "write", "update", "delete"])
            ]),
            RolePermission(role="Manager", permissions=[
                Permission(resource="users", actions=["read"]),
                Permission(resource="contacts", actions=["read", "write", "update"]),
                Permission(resource="deals", actions=["read", "write", "update"]),
                Permission(resource="payments", actions=["read"])
            ]),
            RolePermission(role="User", permissions=[
                Permission(resource="contacts", actions=["read", "write"]),
                Permission(resource="deals", actions=["read", "write"]),
                Permission(resource="payments", actions=["read"])
            ])
        ]
        premium_features = ["Analytics", "Invite new workspace user"]

    elif "task" in prompt_lower or "project" in prompt_lower:
        app_name = "Task Management"
        app_type = "Task Manager"
        entities = ["User", "Team", "Project", "Task", "Comment"]
        features = ["login", "dashboard", "teams", "projects", "tasks", "comments"]
        roles = ["Manager", "Member", "Guest"]
        constraints = ["managers can assign tasks", "read-only for guests"]
        assumptions = ["Email alerts for task assignments", "File uploads handled via AWS S3"]
        ambiguities = ["Should guests see comments?"]
        
        tables = [
            DBTable(name="users", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="username", type="VARCHAR(255)", nullable=False),
                DBColumn(name="email", type="VARCHAR(255)", nullable=False, unique=True),
                DBColumn(name="role", type="VARCHAR(50)", nullable=False),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ]),
            DBTable(name="teams", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="name", type="VARCHAR(100)", nullable=False),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ]),
            DBTable(name="projects", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="name", type="VARCHAR(100)", nullable=False),
                DBColumn(name="team_id", type="INTEGER", nullable=False, foreign_key="teams.id"),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ]),
            DBTable(name="tasks", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="title", type="VARCHAR(255)", nullable=False),
                DBColumn(name="description", type="TEXT", nullable=True),
                DBColumn(name="project_id", type="INTEGER", nullable=False, foreign_key="projects.id"),
                DBColumn(name="assigned_to", type="INTEGER", nullable=True, foreign_key="users.id"),
                DBColumn(name="status", type="VARCHAR(50)", nullable=False),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ]),
            DBTable(name="comments", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="task_id", type="INTEGER", nullable=False, foreign_key="tasks.id"),
                DBColumn(name="user_id", type="INTEGER", nullable=False, foreign_key="users.id"),
                DBColumn(name="body", type="TEXT", nullable=False),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ])
        ]
        
        endpoints = [
            APIEndpoint(path="/api/users", method="GET", description="Get users list", allowed_roles=["Manager", "Member", "Guest"], db_table="users",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="username", type="string"), APIField(name="email", type="string")]),
            APIEndpoint(path="/api/teams", method="GET", description="List teams", allowed_roles=["Manager", "Member"], db_table="teams",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="name", type="string")]),
            APIEndpoint(path="/api/teams", method="POST", description="Create a team", allowed_roles=["Manager"], db_table="teams",
                        request_body=[APIField(name="name", type="string")]),
            APIEndpoint(path="/api/projects", method="GET", description="List team projects", allowed_roles=["Manager", "Member", "Guest"], db_table="projects",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="name", type="string"), APIField(name="team_id", type="integer")]),
            APIEndpoint(path="/api/projects", method="POST", description="Create a project", allowed_roles=["Manager"], db_table="projects",
                        request_body=[APIField(name="name", type="string"), APIField(name="team_id", type="integer")]),
            APIEndpoint(path="/api/tasks", method="GET", description="List tasks", allowed_roles=["Manager", "Member", "Guest"], db_table="tasks",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="title", type="string"), APIField(name="description", type="string"), APIField(name="project_id", type="integer"), APIField(name="assigned_to", type="integer"), APIField(name="status", type="string")]),
            APIEndpoint(path="/api/tasks", method="POST", description="Create task", allowed_roles=["Manager", "Member"], db_table="tasks",
                        request_body=[APIField(name="title", type="string"), APIField(name="project_id", type="integer"), APIField(name="assigned_to", type="integer"), APIField(name="status", type="string")]),
            APIEndpoint(path="/api/comments", method="GET", description="List comments", allowed_roles=["Manager", "Member", "Guest"], db_table="comments",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="task_id", type="integer"), APIField(name="user_id", type="integer"), APIField(name="body", type="string")]),
            APIEndpoint(path="/api/comments", method="POST", description="Add comment", allowed_roles=["Manager", "Member"], db_table="comments",
                        request_body=[APIField(name="task_id", type="integer"), APIField(name="user_id", type="integer"), APIField(name="body", type="string")])
        ]
        
        pages = [
            UIPage(name="Dashboard", route="/dashboard", accessible_by=["Manager", "Member", "Guest"], components=[
                UIComponent(type="card", label="Workspace Overview"),
                UIComponent(type="table", label="Active Tasks List", api_endpoint="/api/tasks")
            ]),
            UIPage(name="Projects", route="/projects", accessible_by=["Manager", "Member", "Guest"], components=[
                UIComponent(type="table", label="Projects list summary", api_endpoint="/api/projects"),
                UIComponent(type="form", label="Create Project", api_endpoint="/api/projects", fields=["name", "team_id"])
            ]),
            UIPage(name="Tasks", route="/tasks", accessible_by=["Manager", "Member", "Guest"], components=[
                UIComponent(type="table", label="Detailed Tasks Board", api_endpoint="/api/tasks"),
                UIComponent(type="form", label="Create Task Form", api_endpoint="/api/tasks", fields=["title", "project_id", "assigned_to", "status"])
            ]),
            UIPage(name="Teams", route="/teams", accessible_by=["Manager", "Member"], components=[
                UIComponent(type="table", label="Active Teams list", api_endpoint="/api/teams"),
                UIComponent(type="form", label="Create Team", api_endpoint="/api/teams", fields=["name"])
            ]),
            UIPage(name="Comments", route="/comments", accessible_by=["Manager", "Member", "Guest"], components=[
                UIComponent(type="table", label="Task Comments Thread", api_endpoint="/api/comments"),
                UIComponent(type="form", label="Add Comment Form", api_endpoint="/api/comments", fields=["task_id", "user_id", "body"])
            ])
        ]
        nav = ["Dashboard", "Projects", "Tasks", "Teams"]
        
        relations = [
            EntityRelation(from_entity="projects", to_entity="teams", relation="belongs_to"),
            EntityRelation(from_entity="tasks", to_entity="projects", relation="belongs_to"),
            EntityRelation(from_entity="tasks", to_entity="users", relation="belongs_to"),
            EntityRelation(from_entity="comments", to_entity="tasks", relation="belongs_to"),
            EntityRelation(from_entity="comments", to_entity="users", relation="belongs_to")
        ]
        
        flows = [
            UserFlow(role="Manager", flow=["Dashboard", "Projects", "Create Project", "Tasks", "Create Task Form"]),
            UserFlow(role="Member", flow=["Dashboard", "Tasks", "Comments", "Add Comment Form"]),
            UserFlow(role="Guest", flow=["Dashboard", "Projects", "Tasks"])
        ]
        rules = [
            "Only Manager role can create projects and teams.",
            "Guests have read-only access to dashboard, projects, and tasks."
        ]
        
        role_permissions = [
            RolePermission(role="Manager", permissions=[
                Permission(resource="users", actions=["read"]),
                Permission(resource="teams", actions=["read", "write", "update", "delete"]),
                Permission(resource="projects", actions=["read", "write", "update", "delete"]),
                Permission(resource="tasks", actions=["read", "write", "update", "delete"]),
                Permission(resource="comments", actions=["read", "write", "update", "delete"])
            ]),
            RolePermission(role="Member", permissions=[
                Permission(resource="users", actions=["read"]),
                Permission(resource="teams", actions=["read"]),
                Permission(resource="projects", actions=["read"]),
                Permission(resource="tasks", actions=["read", "write", "update"]),
                Permission(resource="comments", actions=["read", "write", "update"])
            ]),
            RolePermission(role="Guest", permissions=[
                Permission(resource="users", actions=["read"]),
                Permission(resource="projects", actions=["read"]),
                Permission(resource="tasks", actions=["read"]),
                Permission(resource="comments", actions=["read"])
            ])
        ]
        premium_features = ["Create Project", "Create Team"]

    elif "ecommerce" in prompt_lower or "store" in prompt_lower or "shop" in prompt_lower or "product" in prompt_lower:
        app_name = "E-Commerce"
        app_type = "E-commerce"
        entities = ["User", "Product", "CartItem", "Order", "Payment"]
        features = ["login", "dashboard", "products", "orders", "payments", "shopping cart"]
        roles = ["Admin", "Customer", "Guest"]
        constraints = ["admins manage inventory", "guest checkout allowed"]
        assumptions = ["Stripe processes card payments", "Courier API for shipping calculation"]
        ambiguities = ["Should admins handle product reviews?"]
        
        tables = [
            DBTable(name="users", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="username", type="VARCHAR(255)", nullable=False),
                DBColumn(name="email", type="VARCHAR(255)", nullable=False, unique=True),
                DBColumn(name="role", type="VARCHAR(50)", nullable=False),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ]),
            DBTable(name="products", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="name", type="VARCHAR(255)", nullable=False),
                DBColumn(name="price", type="DECIMAL(10,2)", nullable=False),
                DBColumn(name="stock", type="INTEGER", nullable=False),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ]),
            DBTable(name="cart_items", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="user_id", type="INTEGER", nullable=True, foreign_key="users.id"),
                DBColumn(name="product_id", type="INTEGER", nullable=False, foreign_key="products.id"),
                DBColumn(name="quantity", type="INTEGER", nullable=False),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ]),
            DBTable(name="orders", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="user_id", type="INTEGER", nullable=True, foreign_key="users.id"),
                DBColumn(name="total_amount", type="DECIMAL(10,2)", nullable=False),
                DBColumn(name="status", type="VARCHAR(50)", nullable=False),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ]),
            DBTable(name="payments", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="order_id", type="INTEGER", nullable=False, foreign_key="orders.id"),
                DBColumn(name="amount", type="DECIMAL(10,2)", nullable=False),
                DBColumn(name="status", type="VARCHAR(50)", nullable=False),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ])
        ]
        
        endpoints = [
            APIEndpoint(path="/api/users", method="GET", description="Get system users", allowed_roles=["Admin"], db_table="users",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="username", type="string"), APIField(name="email", type="string")]),
            APIEndpoint(path="/api/products", method="GET", description="Browse shop inventory", allowed_roles=["Admin", "Customer", "Guest"], db_table="products",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="name", type="string"), APIField(name="price", type="number"), APIField(name="stock", type="integer")]),
            APIEndpoint(path="/api/products", method="POST", description="Add new product", allowed_roles=["Admin"], db_table="products",
                        request_body=[APIField(name="name", type="string"), APIField(name="price", type="number"), APIField(name="stock", type="integer")]),
            APIEndpoint(path="/api/cart", method="GET", description="Get customer cart", allowed_roles=["Admin", "Customer", "Guest"], db_table="cart_items",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="product_id", type="integer"), APIField(name="quantity", type="integer")]),
            APIEndpoint(path="/api/cart", method="POST", description="Add item to cart", allowed_roles=["Admin", "Customer", "Guest"], db_table="cart_items",
                        request_body=[APIField(name="product_id", type="integer"), APIField(name="quantity", type="integer")]),
            APIEndpoint(path="/api/orders", method="GET", description="List order records", allowed_roles=["Admin", "Customer"], db_table="orders",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="total_amount", type="number"), APIField(name="status", type="string")]),
            APIEndpoint(path="/api/orders", method="POST", description="Checkout new order", allowed_roles=["Admin", "Customer", "Guest"], db_table="orders",
                        request_body=[APIField(name="total_amount", type="number"), APIField(name="status", type="string")]),
            APIEndpoint(path="/api/payments", method="POST", description="Submit payment info", allowed_roles=["Admin", "Customer", "Guest"], db_table="payments",
                        request_body=[APIField(name="order_id", type="integer"), APIField(name="amount", type="number"), APIField(name="status", type="string")])
        ]
        
        pages = [
            UIPage(name="Dashboard", route="/dashboard", accessible_by=["Admin", "Customer", "Guest"], components=[
                UIComponent(type="card", label="Store Welcome Dashboard"),
                UIComponent(type="table", label="Catalog Products", api_endpoint="/api/products")
            ]),
            UIPage(name="Products", route="/products", accessible_by=["Admin", "Customer", "Guest"], components=[
                UIComponent(type="table", label="Manage Products List", api_endpoint="/api/products"),
                UIComponent(type="form", label="Add Product Form", api_endpoint="/api/products", fields=["name", "price", "stock"])
            ]),
            UIPage(name="Cart", route="/cart", accessible_by=["Admin", "Customer", "Guest"], components=[
                UIComponent(type="table", label="My Shopping Cart Details", api_endpoint="/api/cart"),
                UIComponent(type="form", label="Checkout Form details", api_endpoint="/api/orders", fields=["total_amount", "status"])
            ]),
            UIPage(name="Orders", route="/orders", accessible_by=["Admin", "Customer"], components=[
                UIComponent(type="table", label="Order History summary", api_endpoint="/api/orders")
            ])
        ]
        nav = ["Dashboard", "Products", "Cart", "Orders"]
        
        relations = [
            EntityRelation(from_entity="cart_items", to_entity="products", relation="belongs_to"),
            EntityRelation(from_entity="cart_items", to_entity="users", relation="belongs_to"),
            EntityRelation(from_entity="orders", to_entity="users", relation="belongs_to"),
            EntityRelation(from_entity="payments", to_entity="orders", relation="belongs_to")
        ]
        
        flows = [
            UserFlow(role="Admin", flow=["Dashboard", "Products", "Add Product Form", "Orders"]),
            UserFlow(role="Customer", flow=["Dashboard", "Products", "Cart", "Add item to cart", "Checkout Form details"]),
            UserFlow(role="Guest", flow=["Dashboard", "Products", "Cart", "Checkout Form details"])
        ]
        rules = [
            "Only Admin users can modify the product catalog and write products.",
            "Customers and Guests can browse catalog products and create checkout orders."
        ]
        
        role_permissions = [
            RolePermission(role="Admin", permissions=[
                Permission(resource="users", actions=["read"]),
                Permission(resource="products", actions=["read", "write", "update", "delete"]),
                Permission(resource="cart_items", actions=["read", "write", "update", "delete"]),
                Permission(resource="orders", actions=["read", "write", "update", "delete"]),
                Permission(resource="payments", actions=["read", "write", "update", "delete"])
            ]),
            RolePermission(role="Customer", permissions=[
                Permission(resource="products", actions=["read"]),
                Permission(resource="cart_items", actions=["read", "write", "update"]),
                Permission(resource="orders", actions=["read", "write"]),
                Permission(resource="payments", actions=["read", "write"])
            ]),
            RolePermission(role="Guest", permissions=[
                Permission(resource="products", actions=["read"]),
                Permission(resource="cart_items", actions=["read", "write", "update"]),
                Permission(resource="orders", actions=["read", "write"]),
                Permission(resource="payments", actions=["read", "write"])
            ])
        ]
        premium_features = ["Add Product Form"]

    else:
        # Generic fallback generator based on keywords
        words = re.findall(r"\b\w{4,15}\b", prompt_lower)
        nouns = [w.capitalize() for w in words if w not in ["with", "from", "create", "build", "have", "that", "this", "user", "admin", "login", "role", "system", "dashboard"]]
        nouns = list(dict.fromkeys(nouns))[:3]
        if not nouns:
            nouns = ["Item", "Category"]
            
        app_name = nouns[0] + " Manager" if nouns else "Custom App"
        app_type = "Generic Manager"
        entities = ["User"] + nouns
        features = ["login", "dashboard", "reporting"] + [n.lower() + "_management" for n in nouns]
        roles = ["Admin", "User"]
        constraints = ["role-based access control enabled"]
        assumptions = ["Relational SQL database utilized", "RESTful web API architecture style"]
        ambiguities = ["What specific reporting charts are requested?"]
        
        tables = [
            DBTable(name="users", columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="username", type="VARCHAR(255)", nullable=False),
                DBColumn(name="email", type="VARCHAR(255)", nullable=False, unique=True),
                DBColumn(name="role", type="VARCHAR(50)", nullable=False),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ])
        ]
        
        for n in nouns:
            t_name = n.lower() + "s"
            tables.append(DBTable(name=t_name, columns=[
                DBColumn(name="id", type="INTEGER", primary_key=True),
                DBColumn(name="name", type="VARCHAR(255)", nullable=False),
                DBColumn(name="user_id", type="INTEGER", nullable=False, foreign_key="users.id"),
                DBColumn(name="created_at", type="TIMESTAMP", nullable=True)
            ]))
            
        endpoints = [
            APIEndpoint(path="/api/users", method="GET", description="Get workspace users", allowed_roles=["Admin", "User"], db_table="users",
                        response_fields=[APIField(name="id", type="integer"), APIField(name="username", type="string"), APIField(name="role", type="string")])
        ]
        
        for n in nouns:
            t_name = n.lower() + "s"
            endpoints.append(APIEndpoint(path=f"/api/{t_name}", method="GET", description=f"List {t_name}", allowed_roles=["Admin", "User"], db_table=t_name,
                                         response_fields=[APIField(name="id", type="integer"), APIField(name="name", type="string"), APIField(name="user_id", type="integer")]))
            endpoints.append(APIEndpoint(path=f"/api/{t_name}", method="POST", description=f"Add {n}", allowed_roles=["Admin", "User"], db_table=t_name,
                                         request_body=[APIField(name="name", type="string"), APIField(name="user_id", type="integer")]))
            
        pages = [
            UIPage(name="Dashboard", route="/dashboard", accessible_by=["Admin", "User"], components=[
                UIComponent(type="card", label="Home Overview Dashboard")
            ])
        ]
        
        for n in nouns:
            t_name = n.lower() + "s"
            pages.append(UIPage(name=n, route=f"/{t_name}", accessible_by=["Admin", "User"], components=[
                UIComponent(type="table", label=f"Manage {n}", api_endpoint=f"/api/{t_name}"),
                UIComponent(type="form", label=f"Create {n}", api_endpoint=f"/api/{t_name}", fields=["name", "user_id"])
            ]))
            
        nav = ["Dashboard"] + nouns
        
        relations = []
        for n in nouns:
            relations.append(EntityRelation(from_entity=n.lower() + "s", to_entity="users", relation="belongs_to"))
            
        flows = [
            UserFlow(role="Admin", flow=["Dashboard"] + [f"Create {n}" for n in nouns]),
            UserFlow(role="User", flow=["Dashboard"] + [n for n in nouns])
        ]
        
        rules = ["Only authenticated users can access resource elements."]
        
        role_permissions = [
            RolePermission(role="Admin", permissions=[Permission(resource="users", actions=["read", "write", "update", "delete"])] + [Permission(resource=n.lower() + "s", actions=["read", "write", "update", "delete"]) for n in nouns]),
            RolePermission(role="User", permissions=[Permission(resource="users", actions=["read"])] + [Permission(resource=n.lower() + "s", actions=["read", "write"]) for n in nouns])
        ]
        premium_features = []
        
    intent = IntentSchema(
        app_name=app_name,
        app_type=app_type,
        entities=entities,
        features=features,
        roles=roles,
        constraints=constraints,
        assumptions=assumptions,
        ambiguities=ambiguities
    )
    
    design = DesignSchema(
        architecture_type="REST microservices",
        auth_strategy="JWT authorization headers",
        entity_relations=relations,
        user_flows=flows,
        business_rules=rules
    )
    
    db_schema = DBSchema(tables=tables)
    api_schema = APISchema(endpoints=endpoints)
    ui_schema = UISchema(pages=pages, navigation=nav)
    auth_schema = AuthSchema(strategy="JWT session token validation", roles=roles, role_permissions=role_permissions, premium_features=premium_features)
    
    return AppConfig(
        intent=intent,
        design=design,
        db_schema=db_schema,
        api_schema=api_schema,
        ui_schema=ui_schema,
        auth_schema=auth_schema,
        validation_issues=[],
        assumptions=assumptions,
        retries=0,
        repairs=0
    )
