import React, { useState, useEffect, useCallback, useRef } from "react";

// ─── API Configuration (inline — no external imports needed) ─────────────────
const SERVICES = {
  anomaly:    (window as any).REACT_APP_ANOMALY_URL    || "http://localhost:8080",
  resolution: (window as any).REACT_APP_RESOLUTION_URL || "http://localhost:8081",
  audit:      (window as any).REACT_APP_AUDIT_URL      || "http://localhost:8082",
};

// ─── Types ────────────────────────────────────────────────────────────────────
interface ServiceHealth {
  anomaly:    "UP" | "DOWN" | "CHECKING";
  resolution: "UP" | "DOWN" | "CHECKING";
  audit:      "UP" | "DOWN" | "CHECKING";
}

interface AnomalyEvent {
  event_id:   string;
  flight:     string;
  route:      string;
  severity:   "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  anomalies:  string[];
  timestamp:  string;
  raw_record: Record<string, unknown>;
  classification?: {
    irrops_type:          string;
    resolution_agents:    string[];
    estimated_pax_impact: number;
    auto_resolve:         boolean;
    priority_score:       number;
  };
}

interface ResolutionPlan {
  task_id:                       string;
  event_id:                      string;
  flight:                        string;
  resolution_steps:              ResolutionStep[];
  estimated_resolution_time_min: number;
  confidence_score:              number;
  requires_human_approval:       boolean;
  status:                        string;
  created_at:                    string;
}

interface ResolutionStep {
  agent:     string;
  tool:      string;
  rationale: string;
  priority:  number;
  result?:   Record<string, unknown>;
  status?:   "PENDING" | "RUNNING" | "SUCCESS" | "FAILED";
}

interface AgentResult {
  agent:       string;
  tool:        string;
  event_id:    string;
  flight:      string;
  result:      Record<string, unknown>;
  executed_at: string;
}

interface AuditEntry {
  action_id:         string;
  event_id:          string;
  flight:            string;
  agent:             string;
  tool_called:       string;
  proposed_action:   string;
  confidence:        number;
  status:            string;
  approved_by?:      string;
  regulatory_impact?: boolean;
  assessed_at?:      string;
}

interface PendingApproval extends AuditEntry {
  escalated_at: string;
}

// ─── Base fetcher ─────────────────────────────────────────────────────────────
async function apiFetch<T>(url: string, options?: RequestInit, timeoutMs = 30000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return await res.json() as T;
  } finally {
    clearTimeout(timer);
  }
}

// ─── Health Check ─────────────────────────────────────────────────────────────
async function checkHealth(): Promise<ServiceHealth> {
  const check = async (url: string): Promise<"UP" | "DOWN"> => {
    try { await apiFetch(`${url}/health`, {}, 3000); return "UP"; }
    catch { return "DOWN"; }
  };
  const [anomaly, resolution, audit] = await Promise.all([
    check(SERVICES.anomaly), check(SERVICES.resolution), check(SERVICES.audit),
  ]);
  return { anomaly, resolution, audit };
}

// ─── API Clients ──────────────────────────────────────────────────────────────
const anomalyApi = {
  scan: () => apiFetch<{ anomalies_detected: number; events: AnomalyEvent[] }>(`${SERVICES.anomaly}/scan`),
  classify: (eventId: string) => apiFetch<any>(`${SERVICES.anomaly}/classify/${eventId}`),
  publish: (eventId: string, priority: number, agents: string[]) =>
    apiFetch<any>(`${SERVICES.anomaly}/publish`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ event_id: eventId, priority, agents }) }),
};

const resolutionApi = {
  decompose: (event: { event_id: string; flight: string; irrops_type: string; severity: string }) =>
    apiFetch<ResolutionPlan>(`${SERVICES.resolution}/decompose`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(event) }),
  executeStep: (agent: string, tool: string, eventId: string, flight: string) =>
    apiFetch<AgentResult>(`${SERVICES.resolution}/execute`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ agent, tool, event_id: eventId, flight }) }),
  getTasks: () => apiFetch<{ tasks: ResolutionPlan[] }>(`${SERVICES.resolution}/tasks`),
};

const auditApi = {
  assessAndRoute: (action: { action_id: string; event_id: string; flight: string; agent: string; tool_called: string; proposed_action: string; regulatory_impact?: boolean }) =>
    apiFetch<{ decision: string; confidence: number; message: string }>(`${SERVICES.audit}/assess`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(action) }),
  getPending: () => apiFetch<{ pending_count: number; actions: PendingApproval[] }>(`${SERVICES.audit}/pending`),
  approve: (actionId: string, controllerId: string, notes?: string) =>
    apiFetch<any>(`${SERVICES.audit}/approve/${actionId}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ controller_id: controllerId, notes: notes || "" }) }),
  reject: (actionId: string, controllerId: string, reason: string) =>
    apiFetch<any>(`${SERVICES.audit}/reject/${actionId}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ controller_id: controllerId, reason }) }),
  getAuditLog: () => apiFetch<{ entries: AuditEntry[] }>(`${SERVICES.audit}/audit-log`),
  getReport: () => apiFetch<Record<string, unknown>>(`${SERVICES.audit}/report`),
};

// ─── Shared Components ────────────────────────────────────────────────────────
const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const map: Record<string, { bg: string; color: string }> = {
    LOW:      { bg: "#f0fdf4", color: "#16a34a" },
    MEDIUM:   { bg: "#fffbeb", color: "#d97706" },
    HIGH:     { bg: "#fff1f2", color: "#e11d48" },
    CRITICAL: { bg: "#faf5ff", color: "#7c3aed" },
  };
  const s = map[severity] || map.MEDIUM;
  return <span style={{ ...s, padding: "2px 8px", borderRadius: 4, fontSize: 10, fontWeight: 700, fontFamily: "monospace", letterSpacing: 1 }}>{severity}</span>;
};

const StatusPill: React.FC<{ status: string }> = ({ status }) => {
  const map: Record<string, { bg: string; color: string; dot: string }> = {
    PENDING:             { bg: "#f1f5f9", color: "#475569", dot: "#94a3b8" },
    RUNNING:             { bg: "#eff6ff", color: "#1d4ed8", dot: "#3b82f6" },
    SUCCESS:             { bg: "#f0fdf4", color: "#16a34a", dot: "#22c55e" },
    FAILED:              { bg: "#fff1f2", color: "#e11d48", dot: "#f43f5e" },
    AUTO_APPROVED:       { bg: "#f0fdf4", color: "#16a34a", dot: "#22c55e" },
    CONTROLLER_APPROVED: { bg: "#f0fdf4", color: "#16a34a", dot: "#22c55e" },
    CONTROLLER_REJECTED: { bg: "#fff1f2", color: "#e11d48", dot: "#f43f5e" },
    PENDING_APPROVAL:    { bg: "#fffbeb", color: "#d97706", dot: "#f59e0b" },
    ESCALATED:           { bg: "#faf5ff", color: "#7c3aed", dot: "#8b5cf6" },
  };
  const s = map[status] || { bg: "#f1f5f9", color: "#475569", dot: "#94a3b8" };
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 5, ...s, padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600 }}>
      <span style={{ width: 6, height: 6, borderRadius: "50%", background: s.dot }} />
      {status.replace(/_/g, " ")}
    </span>
  );
};

const AgentChip: React.FC<{ agent: string }> = ({ agent }) => {
  const map: Record<string, { color: string; bg: string; icon: string }> = {
    ORCHESTRATOR: { color: "#1e3a8a", bg: "#eff6ff", icon: "🧠" },
    FLIGHT_AGENT: { color: "#0369a1", bg: "#f0f9ff", icon: "✈️" },
    CREW_AGENT:   { color: "#166534", bg: "#f0fdf4", icon: "👨‍✈️" },
    OPS_AGENT:    { color: "#581c87", bg: "#faf5ff", icon: "🚪" },
  };
  const s = map[agent] || { color: "#374151", bg: "#f9fafb", icon: "🤖" };
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 4, ...s, padding: "2px 8px", borderRadius: 4, fontSize: 11, fontWeight: 700, fontFamily: "monospace" }}>
      {s.icon} {agent.replace(/_/g, " ")}
    </span>
  );
};

const SectionHeader: React.FC<{ num: string; title: string; subtitle: string; accent: string; live?: boolean; badge?: string }> = ({ num, title, subtitle, accent, live, badge }) => (
  <div style={{ borderBottom: `3px solid ${accent}`, paddingBottom: 16, marginBottom: 28 }}>
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8, flexWrap: "wrap" }}>
      <span style={{ background: accent, color: "#fff", fontFamily: "monospace", fontWeight: 700, fontSize: 11, padding: "4px 10px", borderRadius: 6, letterSpacing: 1 }}>DEMO {num}</span>
      {live && <span style={{ display: "inline-flex", alignItems: "center", gap: 5, color: "#dc2626", fontSize: 11, fontWeight: 700 }}><span style={{ width: 7, height: 7, borderRadius: "50%", background: "#ef4444", display: "inline-block", animation: "pulse 1.4s infinite" }} />LIVE</span>}
      {badge && <span style={{ background: "#f0fdf4", color: "#16a34a", fontFamily: "monospace", fontSize: 10, padding: "2px 8px", borderRadius: 4, border: "1px solid #86efac" }}>{badge}</span>}
    </div>
    <h2 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 22, fontWeight: 700, color: "#0f172a", marginBottom: 4 }}>{title}</h2>
    <p style={{ fontSize: 12, color: "#64748b", fontFamily: "monospace" }}>{subtitle}</p>
  </div>
);

const Btn: React.FC<{ onClick: () => void; disabled?: boolean; color: string; children: React.ReactNode; small?: boolean }> = ({ onClick, disabled, color, children, small }) => (
  <button onClick={onClick} disabled={disabled} style={{ background: disabled ? "#94a3b8" : color, color: "#fff", border: "none", borderRadius: 8, padding: small ? "6px 14px" : "10px 20px", fontSize: small ? 12 : 13, fontWeight: 700, cursor: disabled ? "not-allowed" : "pointer", fontFamily: "monospace", transition: "opacity 0.2s", opacity: disabled ? 0.7 : 1 }}>
    {children}
  </button>
);

const ErrorBanner: React.FC<{ message: string }> = ({ message }) => (
  <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, padding: "10px 14px", marginBottom: 16, fontFamily: "monospace", fontSize: 12, color: "#dc2626" }}>⚠ {message}</div>
);

const sectionStyle: React.CSSProperties = { background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: 28, marginBottom: 24, boxShadow: "0 1px 4px rgba(0,0,0,0.05)" };
const cardStyle:    React.CSSProperties = { background: "#fafafa", border: "1px solid #e2e8f0", borderRadius: 8, padding: "12px 16px" };

// ─── Service Status Bar ───────────────────────────────────────────────────────
const ServiceStatusBar: React.FC<{ health: ServiceHealth; onRefresh: () => void }> = ({ health, onRefresh }) => {
  const services = [
    { key: "anomaly"    as const, label: "Anomaly Detector", port: "8080" },
    { key: "resolution" as const, label: "Resolution Agent",  port: "8081" },
    { key: "audit"      as const, label: "Audit Service",     port: "8082" },
  ];
  return (
    <div style={{ background: "#f8fafc", borderBottom: "1px solid #e2e8f0", padding: "8px 24px" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <span style={{ fontFamily: "monospace", fontSize: 10, color: "#6b7280", letterSpacing: 2 }}>MCP SERVICES</span>
        {services.map(s => {
          const status = health[s.key];
          const color  = status === "UP" ? "#16a34a" : status === "DOWN" ? "#dc2626" : "#d97706";
          const bg     = status === "UP" ? "#f0fdf4" : status === "DOWN" ? "#fef2f2" : "#fffbeb";
          return (
            <div key={s.key} style={{ display: "flex", alignItems: "center", gap: 6, background: bg, border: `1px solid ${color}30`, borderRadius: 6, padding: "3px 10px" }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: color, display: "inline-block", animation: status === "CHECKING" ? "pulse 1s infinite" : "none" }} />
              <span style={{ fontFamily: "monospace", fontSize: 10, color, fontWeight: 700 }}>{s.label}</span>
              <span style={{ fontFamily: "monospace", fontSize: 9, color: "#9ca3af" }}>:{s.port}</span>
            </div>
          );
        })}
        <button onClick={onRefresh} style={{ marginLeft: "auto", background: "none", border: "1px solid #e2e8f0", borderRadius: 6, padding: "3px 10px", fontFamily: "monospace", fontSize: 10, color: "#6b7280", cursor: "pointer" }}>↻ Refresh</button>
        {Object.values(health).some(h => h === "DOWN") && (
          <span style={{ fontFamily: "monospace", fontSize: 10, color: "#dc2626", background: "#fef2f2", padding: "3px 8px", borderRadius: 4 }}>⚠ Some services offline — running in demo mode</span>
        )}
      </div>
    </div>
  );
};

// ─── Demo 1: Anomaly Detection ────────────────────────────────────────────────
const AnomalyDemo: React.FC<{ serviceUp: boolean }> = ({ serviceUp }) => {
  const [events, setEvents]       = useState<AnomalyEvent[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [scanCount, setScanCount] = useState(0);
  const [error, setError]         = useState<string | null>(null);
  const [loading, setLoading]     = useState(false);
  const intervalRef               = useRef<NodeJS.Timeout | null>(null);

  const MOCK_FLIGHTS = ["AA-301","UA-445","DL-892","SW-1201","BA-178","LH-454"];
  const MOCK_ROUTES  = ["JFK→LAX","ORD→MIA","DFW→SEA","ATL→BOS","LHR→JFK","FRA→ORD"];
  const MOCK_SEVS    = ["LOW","MEDIUM","HIGH","CRITICAL"] as AnomalyEvent["severity"][];
  const MOCK_ANOMS   = [["DELAY: 140min detected"],["CREW_ISSUE: NO_SHOW"],["WEATHER_ALERT: STORM"],["DELAY: 55min","CREW_ISSUE: SICK"]];

  const doScan = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      if (serviceUp) {
        const data = await anomalyApi.scan();
        if (data.events.length > 0) { setEvents(prev => [...data.events, ...prev].slice(0,15)); setScanCount(c => c + data.anomalies_detected); }
      } else {
        const i = Math.floor(Math.random() * MOCK_FLIGHTS.length);
        const mock: AnomalyEvent = { event_id: `EVT-${Date.now()}-DEMO`, flight: MOCK_FLIGHTS[i], route: MOCK_ROUTES[i], severity: MOCK_SEVS[Math.floor(Math.random()*4)], anomalies: MOCK_ANOMS[Math.floor(Math.random()*4)], timestamp: new Date().toISOString(), raw_record: { demo: true } };
        setEvents(prev => [mock, ...prev].slice(0,15)); setScanCount(c => c+1);
      }
    } catch(e: any) { setError(`Scan failed: ${e.message}`); }
    finally { setLoading(false); }
  }, [serviceUp]);

  const startStream = useCallback(() => { setStreaming(true); doScan(); intervalRef.current = setInterval(doScan, 4000); }, [doScan]);
  const stopStream  = useCallback(() => { setStreaming(false); if (intervalRef.current) clearInterval(intervalRef.current); }, []);
  useEffect(() => () => { if (intervalRef.current) clearInterval(intervalRef.current); }, []);

  return (
    <section style={sectionStyle}>
      <SectionHeader num="01" title="Real-Time Anomaly Detection Pipeline" subtitle={`Pub/Sub → Vertex AI Gemini → MCP Tool Dispatch  |  ${serviceUp ? "🟢 Live API" : "🟡 Demo Mode"}`} accent="#1d4ed8" live={streaming} badge={serviceUp ? "VERTEX AI ACTIVE" : undefined} />
      <div style={{ display:"flex", alignItems:"center", gap:0, marginBottom:24, overflowX:"auto", padding:"8px 0" }}>
        {["ACARS/AODB","Crew Rosters","Weather Feeds","Pub/Sub","Anomaly Detector","MCP Registry","Agents"].map((n,i,arr) => (
          <React.Fragment key={n}>
            <div style={{ background: i===4?"#1d4ed8":"#f8fafc", border:`1.5px solid ${i===4?"#1d4ed8":"#e2e8f0"}`, borderRadius:7, padding:"6px 12px", fontSize:10, fontWeight:600, color:i===4?"#fff":"#374151", whiteSpace:"nowrap", fontFamily:"monospace" }}>{n}</div>
            {i<arr.length-1 && <div style={{ width:16, height:1, background:"#cbd5e1", flexShrink:0, position:"relative" }}><span style={{ position:"absolute", right:-3, top:-5, fontSize:9, color:"#94a3b8" }}>▶</span></div>}
          </React.Fragment>
        ))}
      </div>
      {error && <ErrorBanner message={error} />}
      <div style={{ display:"flex", gap:10, marginBottom:20, alignItems:"center", flexWrap:"wrap" }}>
        <Btn onClick={streaming ? stopStream : startStream} color={streaming?"#dc2626":"#1d4ed8"}>{streaming ? "⏹ Stop Stream" : "▶ Start Live Stream"}</Btn>
        <Btn onClick={doScan} disabled={loading||streaming} color="#0369a1" small>{loading ? "⏳ Scanning..." : "⚡ Single Scan"}</Btn>
        <span style={{ fontFamily:"monospace", fontSize:12, color:"#64748b" }}>{scanCount} anomalies ingested</span>
      </div>
      <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
        {events.length===0 && <div style={{ textAlign:"center", padding:"40px 0", color:"#94a3b8", fontFamily:"monospace", fontSize:13 }}>Press "Start Live Stream" to begin ingesting IRROPS events</div>}
        {events.map((ev,i) => (
          <div key={ev.event_id} style={{ ...cardStyle, borderLeft:`4px solid ${ev.severity==="CRITICAL"?"#7c3aed":ev.severity==="HIGH"?"#e11d48":ev.severity==="MEDIUM"?"#d97706":"#16a34a"}`, opacity:i===0?1:0.88 }}>
            <div style={{ display:"flex", justifyContent:"space-between", flexWrap:"wrap", gap:8 }}>
              <div style={{ display:"flex", gap:8, alignItems:"center", flexWrap:"wrap" }}>
                <span style={{ fontFamily:"monospace", fontWeight:700, fontSize:14 }}>{ev.flight}</span>
                <span style={{ fontFamily:"monospace", fontSize:12, color:"#64748b" }}>{ev.route}</span>
              </div>
              <SeverityBadge severity={ev.severity} />
            </div>
            <div style={{ marginTop:6, fontFamily:"monospace", fontSize:11, color:"#64748b" }}>{ev.anomalies.map((a,j) => <div key={j}>• {a}</div>)}</div>
            {ev.classification && (
              <div style={{ marginTop:8, background:"#f0f9ff", border:"1px solid #bae6fd", borderRadius:6, padding:"6px 10px", display:"flex", gap:12, flexWrap:"wrap", fontSize:11, fontFamily:"monospace" }}>
                <span>🤖 <b>Gemini:</b> {ev.classification.irrops_type}</span>
                <span>👥 {ev.classification.estimated_pax_impact} pax</span>
                <span>⚡ Priority {ev.classification.priority_score}/10</span>
                <span style={{ color:ev.classification.auto_resolve?"#16a34a":"#d97706" }}>{ev.classification.auto_resolve?"✓ Auto-resolve":"⚠ Manual review"}</span>
              </div>
            )}
            <div style={{ marginTop:6, fontSize:11, color:"#94a3b8", fontFamily:"monospace" }}>🕐 {new Date(ev.timestamp).toLocaleTimeString()} · {ev.event_id}</div>
          </div>
        ))}
      </div>
    </section>
  );
};

// ─── Demo 2: Multi-Agent Resolution ──────────────────────────────────────────
const ResolutionDemo: React.FC<{ serviceUp: boolean }> = ({ serviceUp }) => {
  const [plan, setPlan]           = useState<ResolutionPlan | null>(null);
  const [steps, setSteps]         = useState<ResolutionStep[]>([]);
  const [resolving, setResolving] = useState(false);
  const [error, setError]         = useState<string | null>(null);

  const triggerResolution = useCallback(async () => {
    setResolving(true); setError(null); setPlan(null); setSteps([]);
    const events = [
      { event_id:`EVT-${Date.now()}`, flight:"UA-445", irrops_type:"CREW_SHORTAGE", severity:"CRITICAL" },
      { event_id:`EVT-${Date.now()}`, flight:"DL-892", irrops_type:"WEATHER_HOLD",  severity:"HIGH" },
      { event_id:`EVT-${Date.now()}`, flight:"AA-301", irrops_type:"DELAY",          severity:"MEDIUM" },
    ];
    const event = events[Math.floor(Math.random()*events.length)];
    try {
      let resolvedPlan: ResolutionPlan;
      if (serviceUp) {
        resolvedPlan = await resolutionApi.decompose(event);
      } else {
        await new Promise(r => setTimeout(r, 1200));
        resolvedPlan = { task_id:`TASK-${Date.now().toString(36).toUpperCase()}`, event_id:event.event_id, flight:event.flight, resolution_steps:[
          { agent:"ORCHESTRATOR", tool:"decompose_irrops",    rationale:"Decompose into actionable sub-tasks",   priority:0, status:"PENDING" },
          { agent:"CREW_AGENT",   tool:"check_fdp_limits",    rationale:"Verify crew legality before reassign",  priority:1, status:"PENDING" },
          { agent:"CREW_AGENT",   tool:"find_available_crew", rationale:"Source replacement crew from reserve",  priority:2, status:"PENDING" },
          { agent:"FLIGHT_AGENT", tool:"rebook_passengers",   rationale:"Reaccommodate affected passengers",     priority:3, status:"PENDING" },
          { agent:"OPS_AGENT",    tool:"update_aodb",         rationale:"Update ops database and notify",        priority:4, status:"PENDING" },
          { agent:"FLIGHT_AGENT", tool:"notify_passengers",   rationale:"Notify all passengers via all channels",priority:5, status:"PENDING" },
        ], estimated_resolution_time_min:45, confidence_score:0.83, requires_human_approval:false, status:"RESOLVING", created_at:new Date().toISOString() };
      }
      setPlan(resolvedPlan);
      setSteps(resolvedPlan.resolution_steps.map(s => ({ ...s, status:"PENDING" as const })));
      for (let i=0; i<resolvedPlan.resolution_steps.length; i++) {
        const step = resolvedPlan.resolution_steps[i];
        setSteps(prev => prev.map((s,j) => j===i ? { ...s, status:"RUNNING" as const } : s));
        await new Promise(r => setTimeout(r, 800 + Math.random()*600));
        try {
          if (serviceUp) {
            const result = await resolutionApi.executeStep(step.agent, step.tool, event.event_id, event.flight);
            setSteps(prev => prev.map((s,j) => j===i ? { ...s, status:"SUCCESS" as const, result:result.result } : s));
          } else {
            setSteps(prev => prev.map((s,j) => j===i ? { ...s, status:"SUCCESS" as const, result:{ status:"SUCCESS" } } : s));
          }
        } catch { setSteps(prev => prev.map((s,j) => j===i ? { ...s, status:"FAILED" as const } : s)); }
      }
    } catch(e: any) { setError(`Resolution failed: ${e.message}`); }
    finally { setResolving(false); }
  }, [serviceUp]);

  const successCount = steps.filter(s => s.status==="SUCCESS").length;
  const progress     = steps.length>0 ? (successCount/steps.length)*100 : 0;

  return (
    <section style={sectionStyle}>
      <SectionHeader num="02" title="Multi-Agent IRROPS Resolution via MCP" subtitle={`Orchestrator → MCP Tool Calls → Specialist Agents  |  ${serviceUp?"🟢 Live API":"🟡 Demo Mode"}`} accent="#16a34a" live={resolving} badge={serviceUp?"GEMINI PRO ACTIVE":undefined} />
      <div style={{ background:"#f8fafc", border:"1px solid #e2e8f0", borderRadius:10, padding:16, marginBottom:24 }}>
        <div style={{ fontFamily:"monospace", fontSize:10, color:"#64748b", marginBottom:10, letterSpacing:2 }}>MCP TOOL CALL ARCHITECTURE</div>
        <div style={{ display:"grid", gridTemplateColumns:"1fr 40px 1fr", gap:12, alignItems:"center" }}>
          <div style={{ background:"#1e3a8a", borderRadius:8, padding:"12px 16px", color:"#fff", textAlign:"center", fontFamily:"monospace" }}>
            <div style={{ fontWeight:700, fontSize:13 }}>🧠 Orchestrator</div>
            <div style={{ fontSize:10, opacity:0.8, marginTop:2 }}>ADK + Gemini Pro</div>
          </div>
          <div style={{ textAlign:"center", fontSize:18, color:"#94a3b8" }}>⇄</div>
          <div style={{ display:"flex", flexDirection:"column", gap:6 }}>
            {[["✈️","Flight Agent","#0369a1"],["👨‍✈️","Crew Agent","#166534"],["🚪","Ops Agent","#581c87"]].map(([icon,label,bg]) => (
              <div key={label as string} style={{ background:bg as string, borderRadius:6, padding:"6px 12px", color:"#fff", fontSize:11, fontWeight:600, fontFamily:"monospace" }}>{icon} {label as string}</div>
            ))}
          </div>
        </div>
      </div>
      {error && <ErrorBanner message={error} />}
      <Btn onClick={triggerResolution} disabled={resolving} color="#16a34a">{resolving?"⏳ Agents Resolving...":"🚨 Trigger IRROPS → Resolve"}</Btn>
      {plan && (
        <div style={{ marginTop:20 }}>
          <div style={{ ...cardStyle, borderLeft:"4px solid #16a34a", marginBottom:16 }}>
            <div style={{ fontFamily:"monospace", fontSize:10, color:"#64748b", letterSpacing:2, marginBottom:6 }}>ACTIVE RESOLUTION TASK</div>
            <div style={{ display:"flex", gap:10, flexWrap:"wrap", alignItems:"center" }}>
              <span style={{ fontFamily:"monospace", fontWeight:700, fontSize:15 }}>{plan.flight}</span>
              <span style={{ fontFamily:"monospace", fontSize:11, color:"#64748b" }}>{plan.task_id}</span>
              <span style={{ fontFamily:"monospace", fontSize:11, background:"#f0fdf4", color:"#16a34a", padding:"2px 8px", borderRadius:4 }}>~{plan.estimated_resolution_time_min}min ETA</span>
              <span style={{ fontFamily:"monospace", fontSize:11 }}>Confidence: <b>{(plan.confidence_score*100).toFixed(0)}%</b></span>
            </div>
            <div style={{ marginTop:12 }}>
              <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, fontFamily:"monospace", color:"#64748b", marginBottom:4 }}>
                <span>Resolution Progress</span><span>{successCount}/{steps.length} steps · {Math.round(progress)}%</span>
              </div>
              <div style={{ height:6, background:"#e2e8f0", borderRadius:3, overflow:"hidden" }}>
                <div style={{ height:"100%", width:`${progress}%`, background:"linear-gradient(90deg,#16a34a,#4ade80)", borderRadius:3, transition:"width 0.6s ease" }} />
              </div>
            </div>
          </div>
          <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
            {steps.map((step,i) => (
              <div key={i} style={{ ...cardStyle, borderLeft:`3px solid ${step.status==="SUCCESS"?"#22c55e":step.status==="RUNNING"?"#3b82f6":step.status==="FAILED"?"#ef4444":"#e2e8f0"}`, opacity:step.status==="PENDING"?0.5:1, transition:"all 0.3s" }}>
                <div style={{ display:"flex", justifyContent:"space-between", marginBottom:6, flexWrap:"wrap", gap:6 }}>
                  <AgentChip agent={step.agent} /><StatusPill status={step.status||"PENDING"} />
                </div>
                <div style={{ fontFamily:"monospace", fontSize:11 }}>
                  <span style={{ color:"#64748b" }}>TOOL: </span><span style={{ color:"#1d4ed8", fontWeight:700 }}>{step.tool}()</span>
                  <span style={{ color:"#94a3b8", marginLeft:10 }}>{step.rationale}</span>
                </div>
                {step.result && step.status==="SUCCESS" && (
                  <div style={{ marginTop:6, background:"#f0fdf4", border:"1px solid #bbf7d0", borderRadius:4, padding:"4px 8px", fontFamily:"monospace", fontSize:10, color:"#166534" }}>
                    ✓ {Object.entries(step.result).filter(([k])=>k!=="status").slice(0,4).map(([k,v])=>`${k}: ${JSON.stringify(v)}`).join(" · ")}
                  </div>
                )}
                {step.status==="RUNNING" && <div style={{ marginTop:6, fontFamily:"monospace", fontSize:10, color:"#3b82f6" }}>⏳ Executing via MCP...</div>}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
};

// ─── Demo 3: Audit & HITL ─────────────────────────────────────────────────────
const AuditDemo: React.FC<{ serviceUp: boolean }> = ({ serviceUp }) => {
  const [pending, setPending]     = useState<PendingApproval[]>([]);
  const [auditLog, setAuditLog]   = useState<AuditEntry[]>([]);
  const [report, setReport]       = useState<any>(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const [rejReason, setRejReason] = useState<Record<string,string>>({});
  const CTRL = "OPS-CTRL-001";
  const FLIGHTS = ["AA-301","UA-445","DL-892","SW-1201","BA-178"];
  const SAMPLE_ACTIONS = [
    { agent:"FLIGHT_AGENT", tool_called:"rebook_passengers",   proposed_action:"Rebook 142 pax on UA-446 departing in 2h",          regulatory_impact:false },
    { agent:"CREW_AGENT",   tool_called:"reassign_crew",       proposed_action:"Assign reserve crew CAP-4471/FO-2281 to DL-892",    regulatory_impact:true  },
    { agent:"OPS_AGENT",    tool_called:"substitute_aircraft", proposed_action:"Substitute B737-MAX8 tail N78544 for SW-1201",       regulatory_impact:false },
    { agent:"FLIGHT_AGENT", tool_called:"cancel_flight",       proposed_action:"Cancel BA-178 and arrange hotel accommodation",      regulatory_impact:true  },
    { agent:"OPS_AGENT",    tool_called:"swap_gate",           proposed_action:"Swap gate B12→C04 for AA-301 departure",            regulatory_impact:false },
  ];

  const simulateActions = useCallback(async () => {
    setLoading(true); setError(null);
    const selected = [...SAMPLE_ACTIONS].sort(()=>Math.random()-0.5).slice(0, Math.floor(Math.random()*3)+2);
    for (const action of selected) {
      const actionId = `ACT-${Date.now()}-${Math.random().toString(36).slice(2,6).toUpperCase()}`;
      const eventId  = `EVT-${Date.now()}`;
      const flight   = FLIGHTS[Math.floor(Math.random()*FLIGHTS.length)];
      try {
        if (serviceUp) {
          const result = await auditApi.assessAndRoute({ action_id:actionId, event_id:eventId, flight, ...action });
          if (result.decision==="ESCALATED") {
            setPending(prev => [{ action_id:actionId, event_id:eventId, flight, ...action, confidence:result.confidence, status:"PENDING_APPROVAL", escalated_at:new Date().toISOString() } as PendingApproval, ...prev]);
          } else {
            setAuditLog(prev => [{ action_id:actionId, event_id:eventId, flight, ...action, confidence:result.confidence, status:"AUTO_APPROVED" } as AuditEntry, ...prev].slice(0,30));
          }
        } else {
          const conf = Math.random()*0.5+0.5;
          await new Promise(r=>setTimeout(r,300));
          if (conf<0.75||action.regulatory_impact) {
            setPending(prev => [{ action_id:actionId, event_id:eventId, flight, ...action, confidence:conf, status:"PENDING_APPROVAL", escalated_at:new Date().toISOString() } as PendingApproval, ...prev]);
          } else {
            setAuditLog(prev => [{ action_id:actionId, event_id:eventId, flight, ...action, confidence:conf, status:"AUTO_APPROVED" } as AuditEntry, ...prev].slice(0,30));
          }
        }
      } catch(e:any) { setError(`Assessment failed: ${e.message}`); }
    }
    setLoading(false);
  }, [serviceUp]);

  const handleApprove = async (actionId: string) => {
    try {
      if (serviceUp) await auditApi.approve(actionId, CTRL);
      const entry = pending.find(p=>p.action_id===actionId);
      if (entry) { setPending(prev=>prev.filter(p=>p.action_id!==actionId)); setAuditLog(prev=>[{ ...entry, status:"CONTROLLER_APPROVED", approved_by:CTRL } as AuditEntry, ...prev].slice(0,30)); }
    } catch(e:any) { setError(`Approve failed: ${e.message}`); }
  };

  const handleReject = async (actionId: string) => {
    try {
      if (serviceUp) await auditApi.reject(actionId, CTRL, rejReason[actionId]||"Controller override");
      const entry = pending.find(p=>p.action_id===actionId);
      if (entry) { setPending(prev=>prev.filter(p=>p.action_id!==actionId)); setAuditLog(prev=>[{ ...entry, status:"CONTROLLER_REJECTED" } as AuditEntry, ...prev].slice(0,30)); }
    } catch(e:any) { setError(`Reject failed: ${e.message}`); }
  };

  const fetchReport = async () => {
    try {
      const r = serviceUp ? await auditApi.getReport() : { report_id:"RPT-DEMO", summary:{ total_actions:auditLog.length+pending.length, auto_approved:auditLog.filter(e=>e.status==="AUTO_APPROVED").length, controller_approved:auditLog.filter(e=>e.status==="CONTROLLER_APPROVED").length, rejected:auditLog.filter(e=>e.status==="CONTROLLER_REJECTED").length, pending:pending.length, avg_confidence:0.81 }, regulatory_compliance:"COMPLIANT" };
      setReport(r);
    } catch(e:any) { setError(`Report failed: ${e.message}`); }
  };

  return (
    <section style={sectionStyle}>
      <SectionHeader num="03" title="Human-in-the-Loop & Regulatory Audit Trail" subtitle={`Confidence scoring → Escalation → Controller approval → BigQuery  |  ${serviceUp?"🟢 Live API":"🟡 Demo Mode"}`} accent="#7c3aed" badge={serviceUp?"BIGQUERY ACTIVE":undefined} />
      {error && <ErrorBanner message={error} />}
      <div style={{ display:"flex", gap:10, marginBottom:24, flexWrap:"wrap" }}>
        <Btn onClick={simulateActions} disabled={loading} color="#7c3aed">{loading?"⏳ Assessing...":"⚡ Simulate Agent Actions"}</Btn>
        <Btn onClick={fetchReport} color="#475569" small>📊 Compliance Report</Btn>
      </div>
      {report && (
        <div style={{ ...cardStyle, borderLeft:"4px solid #7c3aed", marginBottom:20, background:"#faf5ff" }}>
          <div style={{ fontFamily:"monospace", fontSize:10, color:"#7c3aed", letterSpacing:2, marginBottom:8, fontWeight:700 }}>COMPLIANCE REPORT · {report.report_id}</div>
          <div style={{ display:"flex", gap:16, flexWrap:"wrap" }}>
            {Object.entries(report.summary||{}).map(([k,v]) => (
              <div key={k} style={{ textAlign:"center" }}>
                <div style={{ fontFamily:"monospace", fontWeight:700, fontSize:18, color:"#0f172a" }}>{String(v)}</div>
                <div style={{ fontFamily:"monospace", fontSize:9, color:"#64748b", textTransform:"uppercase", letterSpacing:1 }}>{k.replace(/_/g," ")}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop:8, fontFamily:"monospace", fontSize:11 }}>Status: <span style={{ color:report.regulatory_compliance==="COMPLIANT"?"#16a34a":"#dc2626", fontWeight:700 }}>{report.regulatory_compliance}</span></div>
        </div>
      )}
      {pending.length>0 && (
        <div style={{ marginBottom:24 }}>
          <div style={{ fontFamily:"monospace", fontSize:11, letterSpacing:2, color:"#dc2626", fontWeight:700, marginBottom:12, display:"flex", alignItems:"center", gap:8 }}>
            <span style={{ width:8, height:8, borderRadius:"50%", background:"#ef4444", display:"inline-block", animation:"pulse 1.4s infinite" }} />
            PENDING CONTROLLER REVIEW ({pending.length})
          </div>
          <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
            {pending.map(entry => (
              <div key={entry.action_id} style={{ ...cardStyle, borderLeft:"4px solid #e11d48", background:"#fff8f8" }}>
                <div style={{ display:"flex", justifyContent:"space-between", flexWrap:"wrap", gap:8 }}>
                  <div style={{ flex:1 }}>
                    <div style={{ display:"flex", gap:8, alignItems:"center", marginBottom:6, flexWrap:"wrap" }}>
                      <span style={{ fontFamily:"monospace", fontWeight:700 }}>{entry.flight}</span>
                      <AgentChip agent={entry.agent} />
                      <span style={{ fontFamily:"monospace", fontSize:11, color:"#7c3aed" }}>{entry.tool_called}()</span>
                    </div>
                    <div style={{ fontFamily:"monospace", fontSize:11, color:"#374151", marginBottom:4 }}>📋 {entry.proposed_action}</div>
                    <div style={{ display:"flex", gap:8, flexWrap:"wrap", alignItems:"center" }}>
                      <span style={{ fontFamily:"monospace", fontSize:10, color:"#64748b" }}>Confidence: <b style={{ color:entry.confidence<0.6?"#dc2626":"#d97706" }}>{(entry.confidence*100).toFixed(0)}%</b></span>
                      {entry.regulatory_impact && <span style={{ background:"#fffbeb", border:"1px solid #fcd34d", borderRadius:4, padding:"2px 8px", fontSize:10, fontFamily:"monospace", color:"#d97706" }}>⚠️ REGULATORY FLAG</span>}
                    </div>
                    <input placeholder="Rejection reason (optional)" value={rejReason[entry.action_id]||""} onChange={e=>setRejReason(prev=>({...prev,[entry.action_id]:e.target.value}))}
                      style={{ marginTop:8, width:"100%", fontFamily:"monospace", fontSize:11, padding:"5px 8px", border:"1px solid #e2e8f0", borderRadius:4, outline:"none" }} />
                  </div>
                  <div style={{ display:"flex", gap:8, alignItems:"flex-start" }}>
                    <button onClick={()=>handleApprove(entry.action_id)} style={{ background:"#16a34a", color:"#fff", border:"none", borderRadius:6, padding:"8px 16px", fontWeight:700, cursor:"pointer", fontFamily:"monospace", fontSize:12 }}>✓ Approve</button>
                    <button onClick={()=>handleReject(entry.action_id)} style={{ background:"#dc2626", color:"#fff", border:"none", borderRadius:6, padding:"8px 16px", fontWeight:700, cursor:"pointer", fontFamily:"monospace", fontSize:12 }}>✗ Reject</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      {auditLog.length>0 && (
        <div>
          <div style={{ fontFamily:"monospace", fontSize:10, letterSpacing:2, color:"#64748b", fontWeight:700, marginBottom:10 }}>BIGQUERY AUDIT LOG</div>
          <div style={{ border:"1px solid #e2e8f0", borderRadius:8, overflow:"auto" }}>
            <table style={{ width:"100%", borderCollapse:"collapse", fontSize:11, fontFamily:"monospace" }}>
              <thead>
                <tr style={{ background:"#f8fafc", borderBottom:"1px solid #e2e8f0" }}>
                  {["Flight","Agent","Tool","Action","Confidence","Status","Time"].map(h=>(
                    <th key={h} style={{ padding:"10px 12px", textAlign:"left", color:"#64748b", fontWeight:600, fontSize:10, letterSpacing:1, textTransform:"uppercase", whiteSpace:"nowrap" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {auditLog.map((entry,i)=>(
                  <tr key={entry.action_id} style={{ borderBottom:"1px solid #f1f5f9", background:i%2===0?"#fff":"#fafafa" }}>
                    <td style={{ padding:"8px 12px", fontWeight:700 }}>{entry.flight}</td>
                    <td style={{ padding:"8px 12px" }}><AgentChip agent={entry.agent} /></td>
                    <td style={{ padding:"8px 12px", color:"#7c3aed" }}>{entry.tool_called}()</td>
                    <td style={{ padding:"8px 12px", color:"#475569", maxWidth:180 }}><span style={{ display:"block", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{entry.proposed_action}</span></td>
                    <td style={{ padding:"8px 12px" }}>
                      <div style={{ height:4, width:60, background:"#e2e8f0", borderRadius:2, overflow:"hidden" }}>
                        <div style={{ height:"100%", width:`${(entry.confidence||0)*100}%`, background:(entry.confidence||0)>0.75?"#22c55e":"#f59e0b", borderRadius:2 }} />
                      </div>
                      <span style={{ fontSize:9, color:"#94a3b8" }}>{((entry.confidence||0)*100).toFixed(0)}%</span>
                    </td>
                    <td style={{ padding:"8px 12px" }}><StatusPill status={entry.status} /></td>
                    <td style={{ padding:"8px 12px", color:"#94a3b8", fontSize:10 }}>{new Date(entry.assessed_at||Date.now()).toLocaleTimeString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {auditLog.length===0&&pending.length===0&&<div style={{ textAlign:"center", padding:"40px 0", color:"#94a3b8", fontFamily:"monospace", fontSize:13 }}>Press "Simulate Agent Actions" to begin</div>}
    </section>
  );
};

// ─── App Root ─────────────────────────────────────────────────────────────────
const App: React.FC = () => {
  const [health, setHealth] = useState<ServiceHealth>({ anomaly:"CHECKING", resolution:"CHECKING", audit:"CHECKING" });
  const refresh = useCallback(async () => { setHealth({ anomaly:"CHECKING", resolution:"CHECKING", audit:"CHECKING" }); const h = await checkHealth(); setHealth(h); }, []);
  useEffect(() => { refresh(); const t = setInterval(refresh, 30000); return () => clearInterval(t); }, [refresh]);

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&family=IBM+Plex+Mono:wght@400;600;700&display=swap');
        * { box-sizing:border-box; margin:0; padding:0; }
        body { background:#f1f5f9; font-family:'IBM Plex Mono',monospace; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        ::-webkit-scrollbar { width:6px; height:6px; }
        ::-webkit-scrollbar-thumb { background:#cbd5e1; border-radius:3px; }
      `}</style>
      <header style={{ background:"#0f172a", borderBottom:"1px solid #1e293b", padding:"0 24px", position:"sticky", top:0, zIndex:100 }}>
        <div style={{ maxWidth:1100, margin:"0 auto", display:"flex", alignItems:"center", justifyContent:"space-between", height:56 }}>
          <div style={{ display:"flex", alignItems:"center", gap:14 }}>
            <span style={{ fontSize:22 }}>✈️</span>
            <div>
              <div style={{ fontFamily:"'Playfair Display',serif", fontWeight:700, fontSize:16, color:"#f8fafc" }}>IRROPS Agentic AI Platform</div>
              <div style={{ fontFamily:"monospace", fontSize:9, color:"#475569", letterSpacing:2, textTransform:"uppercase" }}>MCP · ADK · Vertex AI · Cloud Run · GCP</div>
            </div>
          </div>
          <div style={{ display:"flex", gap:6 }}>
            {["Python","GCP","ADK","MCP","Gemini"].map(t=>(
              <span key={t} style={{ background:"#1e293b", color:"#64748b", fontFamily:"monospace", fontSize:10, padding:"3px 8px", borderRadius:4 }}>{t}</span>
            ))}
          </div>
        </div>
      </header>
      <ServiceStatusBar health={health} onRefresh={refresh} />
      <div style={{ background:"linear-gradient(135deg,#0f172a 0%,#1e3a8a 50%,#0f172a 100%)", padding:"36px 24px" }}>
        <div style={{ maxWidth:1100, margin:"0 auto" }}>
          <div style={{ fontFamily:"monospace", fontSize:10, color:"#60a5fa", letterSpacing:3, textTransform:"uppercase", marginBottom:10 }}>Enterprise Agentic AI · Airline Operations</div>
          <h1 style={{ fontFamily:"'Playfair Display',serif", fontSize:"clamp(24px,4vw,40px)", fontWeight:800, color:"#f8fafc", lineHeight:1.1, marginBottom:12 }}>Airline IRROPS<br />Agentic AI Platform</h1>
          <p style={{ fontFamily:"monospace", fontSize:12, color:"#64748b", maxWidth:600, lineHeight:1.8 }}>Real-time anomaly detection → MCP-based multi-agent resolution via ADK + Gemini → Human-in-the-loop oversight with BigQuery regulatory audit trail.</p>
          <div style={{ marginTop:20, display:"flex", gap:8, flexWrap:"wrap" }}>
            {[["01","Anomaly Detection","#1d4ed8"],["02","Multi-Agent Resolution","#16a34a"],["03","Audit & Oversight","#7c3aed"]].map(([n,l,c])=>(
              <div key={n as string} style={{ background:"rgba(255,255,255,0.04)", border:`1px solid ${c as string}40`, borderRadius:8, padding:"8px 14px" }}>
                <div style={{ fontFamily:"monospace", fontSize:9, color:c as string, letterSpacing:2, marginBottom:2 }}>DEMO {n as string}</div>
                <div style={{ fontFamily:"monospace", fontSize:11, color:"#cbd5e1" }}>{l as string}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <main style={{ maxWidth:1100, margin:"0 auto", padding:"28px 24px 60px" }}>
        <AnomalyDemo    serviceUp={health.anomaly==="UP"} />
        <ResolutionDemo serviceUp={health.resolution==="UP"} />
        <AuditDemo      serviceUp={health.audit==="UP"} />
      </main>
      <footer style={{ background:"#0f172a", borderTop:"1px solid #1e293b", padding:"20px 24px", textAlign:"center" }}>
        <p style={{ fontFamily:"monospace", fontSize:10, color:"#334155", letterSpacing:2 }}>IRROPS AGENTIC AI PLATFORM · PYTHON · VERTEX AI · ADK · CLOUD RUN · MCP · BIGQUERY</p>
      </footer>
    </>
  );
};

export default App;
