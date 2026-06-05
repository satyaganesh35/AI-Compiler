import { useState } from "react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const SAMPLE_PROMPTS = [
  "Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics.",
  "Create a task management app with teams, projects, tasks, due dates, comments, and file attachments. Managers can assign tasks.",
  "Build an e-commerce store with products, cart, orders, payments, and an admin panel for inventory management.",
];

const STAGES = [
  { key: "stage1_intent", label: "Stage 1", sub: "Intent Extraction" },
  { key: "stage2_design", label: "Stage 2", sub: "System Design" },
  { key: "stage3_schemas", label: "Stage 3", sub: "Schema Generation" },
  { key: "stage4_refine", label: "Stage 4", sub: "Validation + Repair" },
];

const TABS = ["intent", "design", "db_schema", "api_schema", "ui_schema", "auth_schema", "issues"];

function StageBar({ latencies, running, currentStage }) {
  return (
    <div style={{ display: "flex", gap: 8, margin: "24px 0 0" }}>
      {STAGES.map((s, i) => {
        const done = latencies[s.key] !== undefined;
        const active = running && currentStage === i;
        return (
          <div key={s.key} style={{
            flex: 1, padding: "10px 12px",
            borderRadius: 8,
            border: `1px solid ${done ? "#1D9E75" : active ? "#7F77DD" : "#e0e0e0"}`,
            background: done ? "#E1F5EE" : active ? "#EEEDFE" : "#fafafa",
            transition: "all 0.3s"
          }}>
            <div style={{ fontSize: 11, fontWeight: 600, color: done ? "#0F6E56" : active ? "#534AB7" : "#888" }}>
              {s.label}
            </div>
            <div style={{ fontSize: 12, color: done ? "#085041" : active ? "#3C3489" : "#aaa", marginTop: 2 }}>
              {s.sub}
            </div>
            {done && (
              <div style={{ fontSize: 11, color: "#1D9E75", marginTop: 4 }}>
                ✓ {latencies[s.key]}ms
              </div>
            )}
            {active && (
              <div style={{ fontSize: 11, color: "#7F77DD", marginTop: 4 }}>⟳ running...</div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function JSONViewer({ data }) {
  const [collapsed, setCollapsed] = useState({});
  if (!data) return null;

  const fmt = (val, depth = 0) => {
    if (Array.isArray(val)) {
      if (val.length === 0) return <span style={{ color: "#888" }}>[]</span>;
      const key = JSON.stringify(val).slice(0, 20);
      const isCol = collapsed[key + depth];
      return (
        <span>
          <span style={{ cursor: "pointer", color: "#7F77DD", userSelect: "none" }}
            onClick={() => setCollapsed(c => ({ ...c, [key + depth]: !c[key + depth] }))}>
            {isCol ? "▶" : "▼"}
          </span>
          {" ["}
          {isCol
            ? <span style={{ color: "#888", cursor: "pointer" }} onClick={() => setCollapsed(c => ({ ...c, [key + depth]: false }))}>{val.length} items</span>
            : <div style={{ paddingLeft: 16 }}>
              {val.map((item, i) => (
                <div key={i}>{fmt(item, depth + 1)}{i < val.length - 1 ? "," : ""}</div>
              ))}
            </div>
          }
          {"]"}
        </span>
      );
    }
    if (val && typeof val === "object") {
      const entries = Object.entries(val);
      if (entries.length === 0) return <span style={{ color: "#888" }}>{"{}"}</span>;
      const key = Object.keys(val).join(",").slice(0, 20);
      const isCol = collapsed[key + depth];
      return (
        <span>
          <span style={{ cursor: "pointer", color: "#7F77DD", userSelect: "none" }}
            onClick={() => setCollapsed(c => ({ ...c, [key + depth]: !c[key + depth] }))}>
            {isCol ? "▶" : "▼"}
          </span>
          {" {"}
          {isCol
            ? <span style={{ color: "#888", cursor: "pointer" }} onClick={() => setCollapsed(c => ({ ...c, [key + depth]: false }))}>{entries.length} keys</span>
            : <div style={{ paddingLeft: 16 }}>
              {entries.map(([k, v], i) => (
                <div key={k}>
                  <span style={{ color: "#185FA5" }}>"{k}"</span>
                  <span style={{ color: "#444" }}>: </span>
                  {fmt(v, depth + 1)}
                  {i < entries.length - 1 ? "," : ""}
                </div>
              ))}
            </div>
          }
          {"}"}
        </span>
      );
    }
    if (typeof val === "string") return <span style={{ color: "#D85A30" }}>"{val}"</span>;
    if (typeof val === "boolean") return <span style={{ color: "#9933aa" }}>{String(val)}</span>;
    if (val === null) return <span style={{ color: "#888" }}>null</span>;
    return <span style={{ color: "#1D9E75" }}>{String(val)}</span>;
  };

  return (
    <pre style={{
      background: "#f8f8f8", borderRadius: 8, padding: 16, overflowX: "auto",
      fontSize: 12, lineHeight: 1.6, margin: 0, fontFamily: "monospace"
    }}>
      {fmt(data)}
    </pre>
  );
}

export default function App() {
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("intent");
  const [currentStage, setCurrentStage] = useState(-1);
  const [partialLatencies, setPartialLatencies] = useState({});

  const generate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setCurrentStage(0);
    setPartialLatencies({});

    // Simulate stage progression based on typical timing
    const stageTimers = STAGES.map((_, i) =>
      setTimeout(() => setCurrentStage(i + 1), (i + 1) * 8000)
    );

    try {
      const res = await fetch(`${API_BASE}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await res.json();
      stageTimers.forEach(clearTimeout);
      setCurrentStage(-1);
      setPartialLatencies(data.stage_latencies || {});

      if (!data.success) {
        setError(data.error || "Unknown error");
      } else {
        setResult(data);
        setActiveTab("intent");
      }
    } catch (e) {
      stageTimers.forEach(clearTimeout);
      setCurrentStage(-1);
      setError("Could not reach backend. Is it running?");
    } finally {
      setLoading(false);
    }
  };

  const tabData = result?.config ? {
    intent: result.config.intent,
    design: result.config.design,
    db_schema: result.config.db_schema,
    api_schema: result.config.api_schema,
    ui_schema: result.config.ui_schema,
    auth_schema: result.config.auth_schema,
    issues: {
      validation_issues: result.config.validation_issues,
      assumptions: result.config.assumptions,
      retries: result.config.retries,
      repairs: result.config.repairs,
    },
  } : {};

  const issueCount = result?.config?.validation_issues?.length || 0;
  const fixedCount = result?.config?.validation_issues?.filter(i => i.auto_fixed).length || 0;

  return (
    <div style={{ minHeight: "100vh", background: "#f4f3ff", fontFamily: "system-ui, sans-serif" }}>
      {/* Header */}
      <div style={{ background: "#fff", borderBottom: "1px solid #e8e8f0", padding: "0 32px" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", alignItems: "center", height: 56, gap: 12 }}>
          <div style={{ width: 28, height: 28, borderRadius: 8, background: "#7F77DD", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: "#fff", fontSize: 14, fontWeight: 700 }}>⚙</span>
          </div>
          <span style={{ fontWeight: 600, fontSize: 16, color: "#1a1a2e" }}>AI Compiler</span>
          <span style={{ color: "#bbb", margin: "0 4px" }}>|</span>
          <span style={{ fontSize: 13, color: "#888" }}>Natural Language → App Config</span>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 32px" }}>
        {/* Input card */}
        <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e8e8f0", padding: 24, marginBottom: 24 }}>
          <label style={{ fontSize: 13, fontWeight: 600, color: "#444", display: "block", marginBottom: 8 }}>
            Describe your app
          </label>
          <textarea
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            placeholder="Build a CRM with login, contacts, dashboard, role-based access, and premium plan with payments. Admins can see analytics."
            rows={4}
            style={{
              width: "100%", boxSizing: "border-box", padding: "12px 14px", fontSize: 14,
              border: "1px solid #ddd", borderRadius: 8, resize: "vertical", lineHeight: 1.6,
              fontFamily: "inherit", outline: "none"
            }}
          />

          {/* Sample prompts */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
            <span style={{ fontSize: 12, color: "#888", alignSelf: "center" }}>Try:</span>
            {SAMPLE_PROMPTS.map((p, i) => (
              <button key={i} onClick={() => setPrompt(p)} style={{
                fontSize: 12, padding: "4px 10px", borderRadius: 20,
                border: "1px solid #ccc", background: "#f8f8ff", color: "#534AB7",
                cursor: "pointer"
              }}>
                {["CRM", "Task Manager", "E-commerce"][i]}
              </button>
            ))}
          </div>

          <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 16 }}>
            <button
              onClick={generate}
              disabled={loading || !prompt.trim()}
              style={{
                padding: "10px 28px", fontSize: 14, fontWeight: 600,
                background: loading ? "#ccc" : "#7F77DD", color: "#fff",
                border: "none", borderRadius: 8, cursor: loading ? "not-allowed" : "pointer"
              }}
            >
              {loading ? "⟳ Generating..." : "Generate App Config →"}
            </button>
            {result && (
              <button onClick={() => {
                const blob = new Blob([JSON.stringify(result.config, null, 2)], { type: "application/json" });
                const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
                a.download = "app_config.json"; a.click();
              }} style={{
                padding: "10px 20px", fontSize: 13, background: "#f0f0ff",
                border: "1px solid #ccc", borderRadius: 8, cursor: "pointer", color: "#444"
              }}>
                ↓ Download JSON
              </button>
            )}
          </div>

          {/* Stage progress */}
          {(loading || Object.keys(partialLatencies).length > 0) && (
            <StageBar
              latencies={partialLatencies}
              running={loading}
              currentStage={currentStage}
            />
          )}
        </div>

        {/* Error */}
        {error && (
          <div style={{ background: "#fff0f0", border: "1px solid #f5c1c1", borderRadius: 8, padding: 16, marginBottom: 16, color: "#c0392b", fontSize: 14 }}>
            ✕ {error}
          </div>
        )}

        {/* Results */}
        {result?.config && (
          <>
            {/* Summary bar */}
            <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
              {[
                { label: "Total latency", value: `${result.latency_ms}ms`, color: "#7F77DD" },
                { label: "Retries", value: result.config.retries, color: "#185FA5" },
                { label: "Issues found", value: issueCount, color: issueCount > 0 ? "#D85A30" : "#1D9E75" },
                { label: "Auto-repaired", value: fixedCount, color: "#1D9E75" },
              ].map(m => (
                <div key={m.label} style={{
                  flex: 1, background: "#fff", border: "1px solid #e8e8f0",
                  borderRadius: 10, padding: "12px 16px"
                }}>
                  <div style={{ fontSize: 11, color: "#888" }}>{m.label}</div>
                  <div style={{ fontSize: 22, fontWeight: 600, color: m.color, marginTop: 2 }}>{m.value}</div>
                </div>
              ))}
            </div>

            {/* Tabs */}
            <div style={{ background: "#fff", borderRadius: 12, border: "1px solid #e8e8f0", overflow: "hidden" }}>
              <div style={{ display: "flex", borderBottom: "1px solid #e8e8f0", overflowX: "auto" }}>
                {TABS.map(tab => (
                  <button key={tab} onClick={() => setActiveTab(tab)} style={{
                    padding: "12px 18px", fontSize: 13, fontWeight: activeTab === tab ? 600 : 400,
                    color: activeTab === tab ? "#7F77DD" : "#666",
                    background: activeTab === tab ? "#f4f3ff" : "transparent",
                    border: "none", borderBottom: activeTab === tab ? "2px solid #7F77DD" : "2px solid transparent",
                    cursor: "pointer", whiteSpace: "nowrap"
                  }}>
                    {tab === "issues" ? `Issues (${issueCount})` : tab.replace("_", " ")}
                  </button>
                ))}
              </div>
              <div style={{ padding: 20 }}>
                <JSONViewer data={tabData[activeTab]} />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
