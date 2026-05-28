import { createFileRoute } from "@tanstack/react-router";
import { useWaves } from "@/lib/plant/hooks";
import {
  Cpu,
  Settings,
  Layers,
  TriangleAlert,
  Activity,
  Plus,
  Send,
  X,
  Loader2,
  Globe,
  Zap,
  Database,
  User,
  DollarSign,
  HardDrive
} from "lucide-react";
import { useState } from "react";
import { getPlantClient } from "@/lib/plant/client";

export const Route = createFileRoute("/plant/waves")({
  component: WavesView,
});

function elapsed(ts?: number) {
  if (!ts) return "—";
  const s = Math.floor((Date.now() - ts) / 1000);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

function WavesView() {
  const w = useWaves() as any;
  const res = w?.resources || {};

  if (!w) return <div className="font-mono text-sm text-muted-foreground">loading…</div>;

  return (
    <div className="space-y-6">
      {/* Top strip - Critical Metrics */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-6">
        <Stat label="throughput / hr" value={w.throughput_per_hour} icon={Activity} />
        <Stat
          label="GPU Load"
          value={w.wave2.locked ? "high" : "idle"}
          icon={Settings}
          tone={w.wave2.locked ? "gpu" : undefined}
        />
        <Stat
          label="daily cost"
          value={`$${w.budgets?.estimated_cost_usd?.toFixed(2) ?? "0.00"}`}
          icon={DollarSign}
        />
        <Stat
          label="waiting review"
          value={w.waiting_human}
          icon={User}
          tone={w.waiting_human > 0 ? "warn" : "ok"}
        />
        <Stat
          label="bad quality"
          value={w.bad_quality}
          icon={TriangleAlert}
          tone={w.bad_quality > 0 ? "err" : "ok"}
        />
        <Stat
          label="errors / hr"
          value={w.errors_last_hour}
          icon={TriangleAlert}
          tone={w.errors_last_hour > 0 ? "err" : undefined}
        />
      </div>

      {/* Hardware Telemetry Section */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <MetricCard
          icon={Cpu}
          label="CPU Load"
          value={`${res.cpu?.percent ?? 0}%`}
          sub="Parallel Grunts"
        />
        <MetricCard
          icon={Zap}
          label="GPU Temp"
          value={`${res.gpu?.temp ?? 0}°C`}
          sub={w.wave2?.locked ? "VRAM Active" : "Cold"}
        />
        <MetricCard
          icon={Activity}
          label="RAM Usage"
          value={`${res.ram?.percent ?? 0}%`}
          sub={`${Math.round((res.ram?.used || 0) / 1024 / 1024 / 1024)}GB / ${Math.round((res.ram?.total || 0) / 1024 / 1024 / 1024)}GB`}
        />
        <MetricCard
          icon={HardDrive}
          label="Disk Space"
          value={`${res.disk?.percent ?? 0}%`}
          sub="Local Assets"
        />
      </section>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Tier 1: Parallel CPU */}
        <section className="rounded-md border border-border bg-card p-4">
          <header className="mb-3 flex items-center justify-between">
            <div>
              <h3 className="font-serif text-lg">Parallel CPU</h3>
              <p className="text-xs text-muted-foreground">Multi-processing Grunts</p>
            </div>
            <Cpu className="h-4 w-4 text-wave-cpu" strokeWidth={1.5} />
          </header>
          <div className="grid grid-cols-2 gap-2">
            {w.wave1.map((s: any) => (
              <div
                key={s.index}
                className={`rounded-md border p-2 ${
                  s.busy
                    ? "border-wave-cpu/40 bg-wave-cpu/5"
                    : "border-dashed border-border bg-transparent"
                }`}
              >
                <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  <span>grunt #{s.index}</span>
                  {s.busy && <span className="text-wave-cpu">{s.task}</span>}
                </div>
                <div className="mt-1 truncate font-serif text-sm text-foreground">
                  {s.busy ? s.sutta_title : <span className="text-muted-foreground/60">idle</span>}
                </div>
                <div className="mt-1 font-mono text-[10px] text-muted-foreground">
                  {s.busy ? elapsed(s.started_at) : ""}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Tier 2: Sequential GPU */}
        <section className="rounded-md border border-border bg-card p-4">
          <header className="mb-3 flex items-center justify-between">
            <div>
              <h3 className="font-serif text-lg">Sequential GPU</h3>
              <p className="text-xs text-muted-foreground">Single Lock · VRAM Owner</p>
            </div>
            <Zap className={`h-4 w-4 ${w.wave2.locked ? "text-wave-gpu" : "text-muted-foreground"}`} strokeWidth={1.5} />
          </header>

          <div
            className={`rounded-md border p-3 ${
              w.wave2.locked ? "border-wave-gpu/50 bg-wave-gpu/5" : "border-dashed border-border"
            }`}
          >
            <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-widest">
              <span className="text-muted-foreground">current owner</span>
              <span className={w.wave2.vram_loaded ? "text-wave-gpu" : "text-muted-foreground"}>
                vram {w.wave2.vram_loaded ? "active" : "cold"}
              </span>
            </div>
            <div className="mt-2 font-serif text-lg text-foreground truncate">
              {w.wave2.sutta_title ?? <span className="text-muted-foreground/60">unlocked</span>}
            </div>
            <div className="mt-4 grid grid-cols-5 gap-1">
              {(["align", "mcq", "translate", "judge", "dub"] as const).map((stage) => {
                const active = w.wave2.stage === stage;
                return (
                  <div
                    key={stage}
                    className={`rounded-sm border py-1 text-center font-mono text-[9px] uppercase tracking-tighter ${
                      active
                        ? "border-wave-gpu bg-wave-gpu/20 text-wave-gpu font-bold"
                        : "border-border text-muted-foreground/40"
                    }`}
                  >
                    {stage}
                  </div>
                );
              })}
            </div>
            <div className="mt-3 flex items-center justify-between font-mono text-[10px] text-muted-foreground">
              <span>hold: {elapsed(w.wave2.started_at)}</span>
              <span>queue depth: {w.wave2.queue_depth}</span>
            </div>
          </div>

          {/* Factory Economics Moved below the Queue */}
          <div className="mt-6 pt-4 border-t border-border space-y-3">
            <h4 className="font-mono text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Burn Rate</h4>
            <CostRow label="GenAI" value={w.budgets?.breakdown?.genai} icon={Zap} />
            <CostRow label="TTS" value={w.budgets?.breakdown?.tts} icon={Activity} />
            <CostRow label="Cloud" value={w.budgets?.breakdown?.storage} icon={Globe} />
            <div className="mt-2 rounded bg-primary/5 p-2 border border-primary/10 flex justify-between items-center">
               <span className="font-mono text-[9px] uppercase text-muted-foreground">Total</span>
               <span className="font-serif text-sm text-primary font-bold">${w.budgets?.estimated_cost_usd?.toFixed(3)}</span>
            </div>
          </div>
        </section>

        {/* Tier 3: External I/O (The API Heartbeat) */}
        <section className="rounded-md border border-border bg-card p-4">
          <header className="mb-3 flex items-center justify-between">
            <div>
              <h3 className="font-serif text-lg">External I/O</h3>
              <p className="text-xs text-muted-foreground">API Latency · Data Flow</p>
            </div>
            <Globe className="h-4 w-4 text-wave-weaver" strokeWidth={1.5} />
          </header>

          <div className="space-y-2">
            <IoRow
                label="YouTube"
                active={!!w.wave1.find((s: any) => s.task === "download")}
                metric={w.wave1.find((s: any) => s.task === "download") ? "4.2 MB/s" : "—"}
                latency={w.wave1.find((s: any) => s.task === "download") ? "120ms" : ""}
            />
            <IoRow
                label="SuttaCentral"
                active={!!w.wave1.find((s: any) => s.task === "extract")}
                metric={w.wave1.find((s: any) => s.task === "extract") ? "3 req/s" : "—"}
                latency={w.wave1.find((s: any) => s.task === "extract") ? "45ms" : ""}
            />
            <IoRow
                label="Gemini / Ollama"
                active={w.wave2.locked && (w.wave2.stage === "align" || w.wave2.stage === "judge" || w.wave2.stage === "translate" || w.wave2.stage === "mcq")}
                metric={w.wave2.locked ? "85 tok/s" : "—"}
                latency={w.wave2.locked ? "240ms" : ""}
            />
            <IoRow
                label="ElevenLabs"
                active={w.wave2.locked && w.wave2.stage === "dub"}
                metric={w.wave2.locked && w.wave2.stage === "dub" ? "1.2k char/s" : "—"}
                latency={w.wave2.locked && w.wave2.stage === "dub" ? "850ms" : ""}
            />
            <IoRow
                label="GCS Warehouse"
                active={!!w.wave3.pipeline?.seal}
                metric={w.wave3.pipeline?.seal ? "12 MB/s" : "—"}
                latency={w.wave3.pipeline?.seal ? "22ms" : ""}
            />
          </div>

          <div className="mt-4 border-t border-border pt-3">
             <div className="flex items-center justify-between font-mono text-[10px] text-muted-foreground">
                <span className="flex items-center gap-1"><Database size={10} /> Factory Buffer</span>
                <span>{w.wave3.ready_to_seal} units pending</span>
             </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value,
  sub,
  tone,
}: {
  icon: any;
  label: string;
  value: string | number;
  sub: string;
  tone?: "ok" | "err";
}) {
  const color = tone === "err" ? "text-status-err" : "text-foreground";
  return (
    <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between font-mono text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
        <span>{label}</span>
        <Icon size={14} className={tone === "err" ? "text-status-err" : "text-muted-foreground"} />
      </div>
      <div className={`mt-2 font-serif text-3xl ${color}`}>{value}</div>
      <div className="mt-1 text-[10px] uppercase tracking-widest text-muted-foreground">{sub}</div>
    </div>
  );
}

function IoRow({ label, active, metric, latency }: { label: string, active: boolean, metric: string, latency: string }) {
    return (
        <div className={`relative flex items-center justify-between rounded-md border p-2 transition-colors ${active ? "border-wave-weaver/40 bg-wave-weaver/5" : "border-dashed border-border"}`}>
            <div className="flex flex-col gap-0.5">
                <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                    {label}
                </span>
                <span className={`font-mono text-[9px] ${active ? "text-wave-weaver" : "text-muted-foreground/30"}`}>
                    {active ? "STREAMING" : "IDLE"}
                </span>
            </div>
            <div className="text-right">
                <div className={`font-mono text-[11px] font-medium ${active ? "text-foreground" : "text-muted-foreground/40"}`}>
                    {active ? metric : "—"}
                </div>
                <div className="font-mono text-[9px] text-muted-foreground/60">
                    {active ? latency : ""}
                </div>
            </div>
            {active && (
                <div className="absolute bottom-0 left-0 h-0.5 bg-wave-weaver/20 animate-in slide-in-from-left duration-1000 infinite" style={{ width: '100%' }}></div>
            )}
        </div>
    );
}

function CostRow({ label, value, icon: Icon }: { label: string, value: number, icon: any }) {
    return (
        <div className="flex items-center justify-between py-1 border-b border-border/50 last:border-0">
            <div className="flex items-center gap-2">
                <Icon size={12} className="text-muted-foreground" />
                <span className="text-xs text-foreground/80">{label}</span>
            </div>
            <span className="font-mono text-xs font-bold">${(value || 0).toFixed(3)}</span>
        </div>
    );
}

function Stat({
  label,
  value,
  icon: Icon,
  tone,
}: {
  label: string;
  value: string | number;
  icon: typeof Activity;
  tone?: "gpu" | "err" | "warn" | "ok";
}) {
  const color =
    tone === "gpu" ? "text-wave-gpu" :
    tone === "err" ? "text-status-err" :
    tone === "warn" ? "text-amber-500" :
    tone === "ok" ? "text-emerald-500" :
    "text-foreground";
  return (
    <div className="rounded-md border border-border bg-card p-3">
      <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
        <span>{label}</span>
        <Icon className={`h-3.5 w-3.5 ${color}`} strokeWidth={1.5} />
      </div>
      <div className={`mt-1 font-serif text-2xl ${color}`}>{value}</div>
    </div>
  );
}

