import { createFileRoute } from "@tanstack/react-router";
import {
  Users,
  ShoppingBag,
  Zap,
  MessageSquare,
  ShieldCheck,
  TrendingUp,
  Smartphone,
  Bell,
  Clock,
  Server,
  Database
} from "lucide-react";

export const Route = createFileRoute("/plant/app")({
  component: AppConsole,
});

function AppConsole() {
  return (
    <div className="space-y-8 pb-12">
      <header>
        <h2 className="font-serif text-2xl">App Console</h2>
        <p className="text-sm text-muted-foreground">
          Live monitoring of the Dama mobile application and user ecosystem.
        </p>
      </header>

      {/* 1. Global Engagement Strip */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <StatCard icon={Users} label="Active Users" value="1,284" sub="+12% from yesterday" />
        <StatCard icon={Clock} label="Avg. Session" value="14m 22s" sub="Core reading time" />
        <StatCard icon={TrendingUp} label="Retention" value="68%" sub="Day-30 benchmark" />
        <StatCard icon={Zap} label="API Latency" value="42ms" sub="Global average" tone="ok" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Left Column: Storefront & Auth */}
        <div className="space-y-6 lg:col-span-2">
          <section className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
             <div className="bg-secondary/20 px-4 py-3 border-b border-border flex justify-between items-center">
                <h3 className="text-xs font-bold uppercase tracking-widest text-primary flex items-center gap-2">
                   <Database size={14} /> Backend Status
                </h3>
                <span className="text-[10px] font-mono text-muted-foreground uppercase">Real-time Traces</span>
             </div>
             <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <div className="text-[10px] uppercase text-muted-foreground font-bold">Supabase Auth</div>
                  <div className="text-emerald-500 font-bold flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span> ACTIVE</div>
                </div>
                <div className="space-y-2">
                  <div className="text-[10px] uppercase text-muted-foreground font-bold">GCS Warehouse</div>
                  <div className="text-emerald-500 font-bold flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span> CONNECTED</div>
                </div>
                <div className="space-y-2">
                  <div className="text-[10px] uppercase text-muted-foreground font-bold">Edge Latency</div>
                  <div className="text-foreground font-bold font-mono">24ms</div>
                </div>
             </div>
          </section>

          <section className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
             <div className="bg-secondary/20 px-4 py-3 border-b border-border flex justify-between items-center">
                <h3 className="text-xs font-bold uppercase tracking-widest text-primary flex items-center gap-2">
                   <ShoppingBag size={14} /> Storefront & Subscriptions
                </h3>
                <span className="text-[10px] font-mono text-muted-foreground uppercase">Live Status</span>
             </div>
             <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-4">
                   <div className="flex justify-between items-end border-b border-border/50 pb-2">
                      <span className="text-sm text-muted-foreground">App Store (iOS)</span>
                      <span className="text-emerald-500 text-xs font-bold">STABLE</span>
                   </div>
                   <div className="flex justify-between items-end border-b border-border/50 pb-2">
                      <span className="text-sm text-muted-foreground">Play Store (Android)</span>
                      <span className="text-emerald-500 text-xs font-bold">STABLE</span>
                   </div>
                   <div className="flex justify-between items-end border-b border-border/50 pb-2">
                      <span className="text-sm text-muted-foreground">Revenue Cat Sync</span>
                      <span className="text-emerald-500 text-xs font-bold">SYNCED</span>
                   </div>
                </div>
                <div className="bg-black/5 dark:bg-white/5 rounded-lg p-4 flex flex-col justify-center text-center">
                   <div className="text-3xl font-serif">$248.50</div>
                   <div className="text-[10px] uppercase text-muted-foreground mt-1 tracking-tighter">New Revenue (Today)</div>
                </div>
             </div>
          </section>

          <section className="rounded-xl border border-border bg-card overflow-hidden shadow-sm">
             <div className="bg-secondary/20 px-4 py-3 border-b border-border flex justify-between items-center">
                <h3 className="text-xs font-bold uppercase tracking-widest text-primary flex items-center gap-2">
                   <ShieldCheck size={14} /> Identity & Auth (Supabase)
                </h3>
                <span className="text-[10px] font-mono text-muted-foreground uppercase">Real-time Traces</span>
             </div>
             <div className="divide-y divide-border">
                {[
                  { user: "john_metta", event: "Login Success", device: "iPhone 15 Pro", time: "2m ago" },
                  { user: "dhamma_seeker", event: "Password Reset", device: "Pixel 8", time: "15m ago" },
                  { user: "sangha_member", event: "New Sign-up", device: "iPad Air", time: "45m ago", highlight: true },
                ].map((trace, i) => (
                  <div key={i} className={`p-4 flex justify-between items-center hover:bg-secondary/10 transition-colors ${trace.highlight ? "bg-primary/5" : ""}`}>
                     <div className="flex items-center gap-3">
                        <div className="size-8 rounded-full bg-secondary flex items-center justify-center text-[10px] font-bold">
                           {trace.user.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                           <div className="text-xs font-bold">{trace.user}</div>
                           <div className="text-[10px] text-muted-foreground flex items-center gap-1">
                              <Smartphone size={10} /> {trace.device}
                           </div>
                        </div>
                     </div>
                     <div className="text-right">
                        <div className="text-[10px] font-bold uppercase text-primary">{trace.event}</div>
                        <div className="text-[10px] text-muted-foreground">{trace.time}</div>
                     </div>
                  </div>
                ))}
             </div>
          </section>
        </div>

        {/* Right Column: Communications & Maintenance */}
        <div className="space-y-6">
           <section className="rounded-xl border border-border bg-card p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase text-muted-foreground flex items-center gap-2">
                  <Bell size={14} /> Notifications
                </h3>
              </div>
              <div className="space-y-3">
                 <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">FCM Gateway</span>
                    <span className="text-emerald-500 font-bold">ONLINE</span>
                 </div>
                 <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Queued Alerts</span>
                    <span className="font-mono">12 Pending</span>
                 </div>
                 <button className="w-full py-2 bg-secondary/50 rounded-md text-[10px] font-bold uppercase tracking-widest hover:bg-secondary transition-colors">
                    Broadcast Update
                 </button>
              </div>
           </section>

           <section className="rounded-xl border border-border bg-card p-5 space-y-4 shadow-sm">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase text-muted-foreground flex items-center gap-2">
                  <MessageSquare size={14} /> User Feedback
                </h3>
              </div>
              <div className="p-12 text-center text-muted-foreground font-mono text-[10px] border border-dashed border-border rounded-lg">
                 No unread feedback.
              </div>
           </section>

           <section className="rounded-xl border border-border bg-card p-5 space-y-4 shadow-sm bg-primary/5">
              <h3 className="text-xs font-bold uppercase text-primary flex items-center gap-2">
                <Server size={14} /> Maintenance
              </h3>
              <p className="text-[10px] text-muted-foreground leading-relaxed">
                 Scheduled downtime for database optimization is planned for Saturday, 02:00 UTC.
              </p>
              <div className="flex gap-2">
                 <div className="h-1 flex-1 bg-primary/20 rounded-full overflow-hidden">
                    <div className="h-full bg-primary" style={{ width: '85%' }}></div>
                 </div>
              </div>
           </section>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, sub, tone }: { icon: any, label: string, value: string, sub: string, tone?: "ok" | "err" }) {
  return (
    <div className="rounded-xl border border-border bg-card p-4 shadow-sm">
      <div className="flex items-center justify-between font-mono text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
        <span>{label}</span>
        <Icon size={14} className={tone === "ok" ? "text-emerald-500" : "text-muted-foreground"} />
      </div>
      <div className={`mt-2 font-serif text-3xl`}>{value}</div>
      <div className="mt-1 text-[10px] uppercase tracking-widest text-muted-foreground">{sub}</div>
    </div>
  );
}
