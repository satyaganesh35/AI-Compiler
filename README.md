# AI Compiler — Natural Language to Verified App Config

A robust, multi-stage compiler pipeline that converts natural language app descriptions into structured, validated, and executable JSON configurations. 

This repository implements a production-grade compiler architecture with cross-schema validation, a targeted auto-repair loop, and a comprehensive evaluation framework.

---

## 🏗️ Architecture & Pipeline Design

Unlike simple single-prompt generators, this system operates like a traditional software compiler: parsing intent, generating an abstract blueprint, emitting multiple target schemas, and validating/repairing them.

```
       [ User Prompt ]
              │
              ▼
   ┌──────────────────────┐
   │  Stage 1: Parsing    │ ──► Extracts entities, features, roles & constraints
   └──────────────────────┘
              │
              ▼
   ┌──────────────────────┐
   │  Stage 2: Design     │ ──► Builds architectural patterns & user journeys
   └──────────────────────┘
              │
              ▼
   ┌──────────────────────┐
   │  Stage 3: Codegen    │ ──► Generates DB, API, UI, and Auth schemas
   └──────────────────────┘
              │
              ▼
   ┌──────────────────────┐
   │  Stage 4: Validation │ ◄──┐
   └──────────────────────┘    │  Auto-Repair Loop
              │                │  (Targeted schema corrections)
         (Any issues?) ────────┘
              │ No
              ▼
   [ Executable App Config ]
```

### 1. Stage 1: Intent Extraction ([stage1_intent.py](file:///c:/Users/user/Downloads/ai-compiler/ai-compiler/backend/pipeline/stage1_intent.py))
Extracts the core requirements (nouns/entities, verbs/features, user roles, and constraints) into a validated JSON contract using Pydantic. It handles ambiguous inputs by documenting assumptions and identifying gaps.

### 2. Stage 2: System Design ([stage2_design.py](file:///c:/Users/user/Downloads/ai-compiler/ai-compiler/backend/pipeline/stage2_design.py))
Translates the parsed intent into a technical blueprint: designing entity relations (e.g. `belongs_to`, `has_many`), authentication strategies (e.g. `JWT`), and step-by-step user journeys per role.

### 3. Stage 3: Schema Generation ([stage3_schemas.py](file:///c:/Users/user/Downloads/ai-compiler/ai-compiler/backend/pipeline/stage3_schemas.py))
Synthesizes the blueprint into four distinct, interconnected execution layers:
* **Database Schema**: DB tables with primary keys, constraints, and foreign key relations.
* **API Schema**: RESTful endpoints, allowed roles, request bodies, and response fields.
* **UI Schema**: Component definitions (forms, tables, charts) linked directly to API paths.
* **Auth Schema**: Complete RBAC mapping role permissions to resources.

### 4. Stage 4: Validate & Repair ([stage4_refine.py](file:///c:/Users/user/Downloads/ai-compiler/ai-compiler/backend/pipeline/stage4_refine.py))
Performs static analysis across all schemas to guarantee runtime validity:
* **API → DB**: Verifies every API endpoint references a real table.
* **API Request Fields → DB Columns**: Ensures request fields exist as table columns.
* **UI → API**: Confirms frontend components connect to existing routes.
* **UI → Auth**: Validates page route visibility roles against the intent.
* **Execution Simulator ([simulator.py](file:///c:/Users/user/Downloads/ai-compiler/ai-compiler/backend/pipeline/simulator.py))**: Traces user flows step-by-step, validating API access control (RBAC), and simulating DB inserts/updates to catch missing fields or constraint violations.

*If any static or simulation checks fail, the **Repair Engine** targets only the broken layer schema, feeding the validation errors back to Claude for correction rather than retrying the whole pipeline.*

---

## 📊 Evaluation Framework & Metrics

We evaluate the system using 20 benchmark prompts consisting of **10 real-world product prompts** and **10 edge cases** (vague, conflicting, incomplete, and overspecified prompts).

To run the evaluation suite:
```bash
cd backend
.\venv\Scripts\python eval_runner.py
```

### Performance Summary
* **Success Rate**: **95% (19/20 passes)**
* **Average Latency**: **~500ms** (using Mock Mode)
* **Expected Failure Case**: `[e2] Single word` prompt ("a") correctly fails length constraints with a validation error (`Prompt is too vague. Please describe your app in more detail.`).

All runs are appended to [eval_log.jsonl](file:///c:/Users/user/Downloads/ai-compiler/ai-compiler/backend/eval_log.jsonl) and summaries are saved in `eval_report.json`.

---

## ⚡ Mock Mode for Sandbox Runs

To support local developer sandboxes or runs without a paid Anthropic key:
* If the API key is not configured or matches the default UUID placeholder (`99ce84b2-ba26-4c79-9065-3c5cf8a251b8`), the compiler switches to **Mock Mode**.
* It leverages [mock_generator.py](file:///c:/Users/user/Downloads/ai-compiler/ai-compiler/backend/mock_generator.py) to procedurally construct high-fidelity schemas that satisfy all cross-layer checks and simulator routes.

---

## 🛠️ Tradeoffs & Decisions

1. **Quality over Latency**: Sequential pipeline stages (1 ➔ 2 ➔ 3 ➔ 4) were chosen over parallel runs because codegen requires the system design blueprint.
2. **Targeted Repair over Full Retry**: Re-running the entire pipeline on schema validation failure is expensive and slow. Targeted repair isolates only the broken JSON layer.
3. **Pydantic Contracts**: Using strict type parsing at the boundary of each stage ensures that generation drift is contained early in the pipeline.
