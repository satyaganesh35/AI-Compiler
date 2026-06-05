"""
Run all 20 evaluation prompts against the running backend and print a metrics report.
Usage: python eval_runner.py
Make sure the backend is running at http://localhost:8000 first.
"""
import json
import time
import httpx
import os

API_URL = "http://localhost:8000/generate"
EVAL_FILE = "eval_prompts.json"

# Check parent directory or directory of the script if running from backend/
if not os.path.exists(EVAL_FILE):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    possible_path = os.path.join(os.path.dirname(script_dir), "eval_prompts.json")
    if os.path.exists(possible_path):
        EVAL_FILE = possible_path
    elif os.path.exists("../eval_prompts.json"):
        EVAL_FILE = "../eval_prompts.json"


def run_all():
    with open(EVAL_FILE) as f:
        data = json.load(f)

    all_prompts = [
        {"id": p["id"], "label": p["label"], "type": "real", "prompt": p["prompt"]}
        for p in data["real_prompts"]
    ] + [
        {"id": p["id"], "label": p["label"], "type": p["type"], "prompt": p["prompt"]}
        for p in data["edge_cases"]
    ]

    results = []
    for item in all_prompts:
        print(f"[{item['id']}] {item['label']} ({item['type']})...", end=" ", flush=True)
        try:
            resp = httpx.post(API_URL, json={"prompt": item["prompt"]}, timeout=120)
            data = resp.json()
            status = "OK" if data.get("success") else "FAIL"
            latency = data.get("latency_ms", 0)
            retries = data.get("config", {}).get("retries", 0) if data.get("config") else 0
            repairs = data.get("config", {}).get("repairs", 0) if data.get("config") else 0
            issues = len(data.get("config", {}).get("validation_issues", [])) if data.get("config") else 0
            print(f"{status} {latency}ms | retries={retries} repairs={repairs} issues={issues}")
            results.append({**item, "success": data.get("success"), "latency_ms": latency,
                            "retries": retries, "repairs": repairs, "issues": issues,
                            "error": data.get("error")})
        except Exception as e:
            print(f"FAIL ERROR: {e}")
            results.append({**item, "success": False, "latency_ms": 0, "error": str(e)})


        time.sleep(1)  # avoid rate limits

    # Summary
    print("\n" + "=" * 60)
    total = len(results)
    successes = sum(1 for r in results if r["success"])
    real = [r for r in results if r["type"] == "real"]
    edge = [r for r in results if r["type"] != "real"]
    avg_lat = sum(r["latency_ms"] for r in results if r["success"]) / max(successes, 1)

    print(f"Total runs:       {total}")
    print(f"Success rate:     {successes}/{total} ({round(successes/total*100)}%)")
    print(f"  Real prompts:   {sum(1 for r in real if r['success'])}/{len(real)}")
    print(f"  Edge cases:     {sum(1 for r in edge if r['success'])}/{len(edge)}")
    print(f"Avg latency:      {round(avg_lat)}ms")
    print(f"Avg retries:      {round(sum(r.get('retries',0) for r in results)/total, 2)}")
    print(f"Avg repairs:      {round(sum(r.get('repairs',0) for r in results)/total, 2)}")

    failures = [r for r in results if not r["success"]]
    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  [{f['id']}] {f['label']}: {f.get('error','')[:80]}")

    # Save report
    with open("eval_report.json", "w") as f:
        json.dump({"summary": {"total": total, "successes": successes,
                               "success_rate": round(successes/total*100, 1),
                               "avg_latency_ms": round(avg_lat)},
                   "results": results}, f, indent=2)
    print("\nFull report saved to eval_report.json")


if __name__ == "__main__":
    run_all()
