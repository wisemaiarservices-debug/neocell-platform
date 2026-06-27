import * as React from "react";
import { createRoot } from "react-dom/client";
import { Activity, BatteryCharging, FileBarChart, Gauge, LayoutDashboard, Lightbulb, Network, PackageCheck, Radio, Router, Settings, ShieldAlert, ShieldCheck, Zap } from "lucide-react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import "./styles.css";

const API = import.meta.env.VITE_NEOCELL_API_BASE ?? "";
const nav = [
  ["/", "Overview", LayoutDashboard], ["/readiness", "Readiness", Gauge],
  ["/edge", "Edge Gateway", Router], ["/sensor-mesh", "Sensor Mesh", Radio],
  ["/power-water", "Power & Water", Zap], ["/deployment-plans", "Deployment Plans", PackageCheck],
  ["/digital-twin", "Digital Twin", Network], ["/recommendations", "Recommendations", Lightbulb],
  ["/reports", "Reports", FileBarChart], ["/settings", "Settings", Settings],
] as const;
const metrics = [["Readiness", "88/100", "good"], ["Gateway", "100%", "good"], ["Sensor mesh", "96%", "good"], ["Edge battery", "72%", "warn"], ["Latency", "218 ms", "info"], ["Pump", "Nominal", "good"], ["Alarms", "2 open", "warn"], ["Autonomy", "Disabled", "info"]] as const;
const line = ["08", "10", "12", "14", "16", "18"].map((t, i) => ({ t, ms: [102, 110, 152, 218, 190, 144][i], p95: [140, 158, 206, 274, 238, 188][i] }));
const readiness = ["Power availability", "Sensor coverage", "Communications", "Edge compute", "Water / pump integration", "Safety review", "Maintenance access", "Data quality"];
const sensors = ["SN-12 Online 98%", "SN-18 Degraded 41%", "EM-03 Online 99%", "PN-01 Online 96%", "WS-01 Online 97%", "RS-01 Online 95%"];
const recs = [
  ["R-001", "Inspect degraded sensor SN-18", "High", "Field service", "Restores sensor coverage in zone Z-08"],
  ["R-002", "Reserve edge battery before heat peak", "High", "Site operator", "Protects edge compute through 14:00-17:00"],
  ["R-003", "Validate pump node before evening irrigation", "Medium", "Site engineer", "Ensures safe irrigation cycle execution"],
  ["R-004", "Improve gateway redundancy for Zone B", "Medium", "Infrastructure planner", "Reduces downtime risk"],
] as const;

function App() {
  const [path, setPath] = React.useState(location.pathname);
  const [api, setApi] = React.useState(API ? "checking" : "fallback");
  React.useEffect(() => {
    const pop = () => setPath(location.pathname);
    addEventListener("popstate", pop);
    if (API) fetch(`${API}/health`).then(r => r.ok ? r.json() : null).then(j => setApi(j?.status === "ok" ? "ok" : "fallback")).catch(() => setApi("fallback"));
    return () => removeEventListener("popstate", pop);
  }, []);
  const go = (to: string) => { history.pushState({}, "", to); setPath(to); };
  const Page = pages[path] ?? Overview;
  const live = api === "ok";
  return <div className="min-h-screen flex bg-background text-foreground">
    <aside className="hidden md:flex w-56 flex-col border-r border-border bg-panel">
      <div className="p-4 border-b border-border"><b>NeoCell — NOVA Infrastructure</b><div className="text-xs text-muted-foreground">Infrastructure Intelligence</div><Chip text={live ? "Connected" : "Connected / Standby Mode"} tone={live ? "good" : "warn"} /></div>
      <nav className="p-2 flex-1">{nav.map(([to, label, Icon]) => <button key={to} onClick={() => go(to)} className={`nav ${path === to ? "active" : ""}`}><Icon size={16}/>{label}</button>)}</nav>
      <div className="p-3 border-t border-border text-[11px] text-muted-foreground">Operator approval required.<br/>No autonomous physical control.</div>
    </aside>
    <main className="flex-1 min-w-0">
      <header className="border-b border-border bg-panel/80">
        <div className="h-12 px-4 flex items-center gap-3"><Activity size={16} className="text-[var(--neo-green)]"/><b>Field Operations Site</b><span className="text-xs text-muted-foreground hidden lg:inline">NHV-SH-01 / Heatwave infrastructure readiness</span><span className="ml-auto text-xs"><Radio size={13} className="inline mr-1"/>{live ? "Connected" : "Connected / Standby Mode"}</span><ShieldCheck size={15}/></div>
        <div className="px-4 pb-3 flex gap-2 overflow-x-auto">{metrics.map(([a,b,t]) => <Chip key={a} text={`${a}: ${b}`} tone={t}/>)}</div>
      </header>
      <div className="p-4 lg:p-6 space-y-5"><Page /></div>
    </main>
  </div>;
}

function H({ title, body }: { title: string; body: string }) { return <div><div className="eyebrow">NOVA Infrastructure</div><h1>{title}</h1><p className="muted">{body}</p></div>; }
function Panel(p: { title: string; children: React.ReactNode }) { return <section className="panel"><div className="panelHead">{p.title}</div><div className="p-4">{p.children}</div></section>; }
function Chip({ text, tone }: { text: string; tone: string }) { return <span className={`chip ${tone}`}>{text}</span>; }
function Chart() { return <div className="h-56"><ResponsiveContainer><LineChart data={line}><CartesianGrid strokeDasharray="3 3" stroke="#2A3D55"/><XAxis dataKey="t" stroke="#9FB0C7" fontSize={10}/><YAxis stroke="#9FB0C7" fontSize={10}/><Tooltip contentStyle={{background:"#152033",border:"1px solid #2A3D55",color:"#EEF6FF"}}/><Line dataKey="ms" stroke="#3AA7FF" strokeWidth={2}/><Line dataKey="p95" stroke="#F6C445" strokeDasharray="4 3"/></LineChart></ResponsiveContainer></div>; }
function Cards() { return <div className="grid grid-cols-2 md:grid-cols-4 gap-3">{metrics.map(([a,b,t]) => <div className="card" key={a}><small>{a}</small><strong className={t}>{b}</strong></div>)}</div>; }
function Overview() { return <><H title="NeoCell — NOVA Infrastructure" body="AI-ready infrastructure readiness for gateways, sensors, power, water, edge compute, and field deployment planning."/><Cards/><div className="grid xl:grid-cols-2 gap-4"><Panel title="Data latency"><Chart/></Panel><Panel title="Pending approval"><Recommendation r={recs[0]}/></Panel></div></>; }
function Readiness() { return <><H title="Infrastructure readiness - 8 categories" body="What is happening, why it is happening, what happens next, and what the operator should do."/><div className="grid md:grid-cols-2 xl:grid-cols-4 gap-3">{readiness.map((r,i)=><div className="card" key={r}><b>{r}</b><strong>{[84,96,91,88,80,92,86,94][i]}/100</strong><p className="muted">Next action requires operator review.</p></div>)}</div></>; }
function Edge() { return <><H title="Edge Gateway & Compute Mesh" body="Gateways, edge compute, local resilience, and latency posture."/><Panel title="Gateway latency"><Chart/></Panel><Cards/></>; }
function SensorMesh() { return <><H title="Sensor Mesh" body="Field telemetry coverage, data quality, degraded sensors, and quarantine candidates."/><div className="grid md:grid-cols-3 gap-3">{sensors.map(s=><div className="card" key={s}>{s}</div>)}</div></>; }
function PowerWater() { return <><H title="Power & Water Readiness" body="Solar, battery, pump, reservoir, and manual validation posture."/><Cards/><Panel title="Coordination trend"><Chart/></Panel></>; }
function DeploymentPlans() { return <><H title="NeoCell Deployment Plans" body="NC-A Lite, Energy, Water, and Full rollout paths."/><div className="grid md:grid-cols-4 gap-3">{["NC-A Lite","NC-A Energy","NC-A Water","NC-A Full"].map(p=><div className="card" key={p}><b>{p}</b><p className="muted">Approval-gated deployment package.</p></div>)}</div></>; }
function DigitalTwin() { return <><H title="Digital Twin" body="Dependency chain from generation to operator-facing impact reports."/><Panel title="Infrastructure chain">{["Solar Array","Battery","Edge Gateway","Pump Node","Field Zone","Impact Report"].map(x=><p key={x}><Network size={14} className="inline mr-2"/>{x}</p>)}</Panel></>; }
function Recommendations() { return <><H title="Recommendations" body="Approval-gated operational recommendations. Physical action remains manual."/><div className="grid lg:grid-cols-2 gap-3">{recs.map(r=><Recommendation key={r[0]} r={r}/>)}</div></>; }
function Reports() { return <><H title="Reports" body="Readiness, operational decisions, risk posture, compliance, and impact."/><Cards/><Panel title="Compliance">All actuator-bearing plans are gated behind operator approval, certified installation, and site engineer validation.</Panel></>; }
function SettingsPage() { return <><H title="Settings" body="Service connection, route map, and safety posture."/><Panel title="Runtime"><p>VITE_NEOCELL_API_BASE: {API || "unset"}</p><p>Connection mode: {API ? "standby available if service is unavailable" : "standby active"}</p><p>No autonomous physical control.</p></Panel></>; }
function Recommendation({ r }: { r: typeof recs[number] }) { return <div className="card"><b>{r[1]}</b><p className="muted">{r[4]}</p><p><ShieldAlert size={14} className="inline mr-1 text-[var(--neo-gold)]"/>Operator approval required / Owner: {r[3]}</p></div>; }

const pages: Record<string, () => React.ReactElement> = {"/":Overview,"/readiness":Readiness,"/edge":Edge,"/sensor-mesh":SensorMesh,"/power-water":PowerWater,"/deployment-plans":DeploymentPlans,"/digital-twin":DigitalTwin,"/recommendations":Recommendations,"/reports":Reports,"/settings":SettingsPage};
createRoot(document.getElementById("root")!).render(<App />);
