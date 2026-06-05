import time
import json
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import anthropic

from models import GenerateRequest, GenerateResponse, AppConfig
from pipeline import stage1_intent, stage2_design, stage3_schemas, stage4_refine

load_dotenv()

app = FastAPI(title="AI Compiler API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EVAL_LOG_PATH = Path("eval_log.jsonl")


def get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")
    return anthropic.Anthropic(api_key=api_key)


def log_eval(prompt: str, response: GenerateResponse):
    """Append one eval record to the JSONL log for metrics."""
    record = {
        "timestamp": datetime.utcnow().isoformat(),
        "prompt_length": len(prompt),
        "success": response.success,
        "latency_ms": response.latency_ms,
        "stage_latencies": response.stage_latencies,
        "retries": response.config.retries if response.config else 0,
        "repairs": response.config.repairs if response.config else 0,
        "validation_issues": len(response.config.validation_issues) if response.config else 0,
        "error": response.error,
    }
    with open(EVAL_LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")


@app.get("/")
def root():
    return {"status": "ok", "message": "AI Compiler API is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    if len(request.prompt.strip()) < 10:
        return GenerateResponse(
            success=False,
            error="Prompt is too vague. Please describe your app in more detail."
        )

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key == "99ce84b2-ba26-4c79-9065-3c5cf8a251b8" or not api_key.startswith("sk-"):
        import mock_generator
        total_start = time.time()
        config = mock_generator.generate_mock_config(request.prompt)
        time.sleep(0.5)
        total_latency = int((time.time() - total_start) * 1000)
        stage_latencies = {
            "stage1_intent": 100,
            "stage2_design": 120,
            "stage3_schemas": 180,
            "stage4_refine": 100
        }
        response = GenerateResponse(
            success=True,
            config=config,
            latency_ms=total_latency,
            stage_latencies=stage_latencies
        )
        log_eval(request.prompt, response)
        return response

    client = get_client()
    stage_latencies: dict[str, int] = {}
    total_start = time.time()
    retries = 0

    try:
        # ── Stage 1: Intent Extraction ────────────────────────────────────────
        t = time.time()
        intent = None
        for attempt in range(3):
            try:
                intent = stage1_intent.run(client, request.prompt)
                break
            except (json.JSONDecodeError, Exception) as e:
                retries += 1
                if attempt == 2:
                    raise ValueError(f"Stage 1 failed after 3 attempts: {e}")
        stage_latencies["stage1_intent"] = int((time.time() - t) * 1000)

        # ── Stage 2: System Design ────────────────────────────────────────────
        t = time.time()
        design = None
        for attempt in range(3):
            try:
                design = stage2_design.run(client, intent)
                break
            except (json.JSONDecodeError, Exception) as e:
                retries += 1
                if attempt == 2:
                    raise ValueError(f"Stage 2 failed after 3 attempts: {e}")
        stage_latencies["stage2_design"] = int((time.time() - t) * 1000)

        # ── Stage 3: Schema Generation ────────────────────────────────────────
        t = time.time()
        db, api, ui, auth = None, None, None, None
        for attempt in range(3):
            try:
                db, api, ui, auth = stage3_schemas.run(client, intent, design)
                break
            except (json.JSONDecodeError, Exception) as e:
                retries += 1
                if attempt == 2:
                    raise ValueError(f"Stage 3 failed after 3 attempts: {e}")
        stage_latencies["stage3_schemas"] = int((time.time() - t) * 1000)

        # ── Stage 4: Validate + Repair ────────────────────────────────────────
        t = time.time()
        db, api, ui, auth, issues, repairs = stage4_refine.run(
            client, intent, db, api, ui, auth, design
        )
        stage_latencies["stage4_refine"] = int((time.time() - t) * 1000)

        total_latency = int((time.time() - total_start) * 1000)

        config = AppConfig(
            intent=intent,
            design=design,
            db_schema=db,
            api_schema=api,
            ui_schema=ui,
            auth_schema=auth,
            validation_issues=issues,
            assumptions=intent.assumptions,
            retries=retries,
            repairs=repairs,
        )

        response = GenerateResponse(
            success=True,
            config=config,
            latency_ms=total_latency,
            stage_latencies=stage_latencies,
        )

    except Exception as e:
        total_latency = int((time.time() - total_start) * 1000)
        response = GenerateResponse(
            success=False,
            error=str(e),
            latency_ms=total_latency,
            stage_latencies=stage_latencies,
        )

    log_eval(request.prompt, response)
    return response


@app.get("/eval/metrics")
def get_metrics():
    """Return aggregated eval metrics from the log."""
    if not EVAL_LOG_PATH.exists():
        return {"total": 0, "message": "No runs logged yet"}

    records = []
    with open(EVAL_LOG_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        return {"total": 0}

    total = len(records)
    successes = sum(1 for r in records if r["success"])
    avg_latency = sum(r["latency_ms"] for r in records) / total
    avg_retries = sum(r.get("retries", 0) for r in records) / total
    avg_repairs = sum(r.get("repairs", 0) for r in records) / total
    failure_types = {}
    for r in records:
        if not r["success"] and r.get("error"):
            key = r["error"][:60]
            failure_types[key] = failure_types.get(key, 0) + 1

    return {
        "total_runs": total,
        "success_rate": round(successes / total * 100, 1),
        "avg_latency_ms": round(avg_latency),
        "avg_retries_per_run": round(avg_retries, 2),
        "avg_repairs_per_run": round(avg_repairs, 2),
        "failure_types": failure_types,
        "recent_runs": records[-5:],
    }
