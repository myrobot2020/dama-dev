import { createFileRoute, Link, Outlet, useRouterState } from "@tanstack/react-router";
import { Moon, Sun, Activity, Layers, Database, BarChart2, Image as ImageIcon, Plus, Send, X, Loader2, Globe } from "lucide-react";
import { useTheme } from "@/hooks/use-theme";
import { useEffect, useState } from "react";
import { getPlantClient } from "@/lib/plant/client";

export const Route = createFileRoute("/plant")({
  head: () => ({
    meta: [
      { title: "Plant — Dama" },
      { name: "description", content: "Tickerplant operations console." },
    ],
  }),
  component: PlantLayout,
});

const tabs = [
  { to: "/plant/waves", label: "Resources", icon: Layers, exact: false },
  { to: "/plant/explorer", label: "Data Explorer", icon: Database, exact: false },
  { to: "/plant/app", label: "App Console", icon: Globe, exact: false },
];

function PlantLayout() {
  const [theme, setTheme] = useTheme();
  const path = useRouterState({ select: (s) => s.location.pathname });

  const [showIngest, setShowIngest] = useState(false);
  const [ingestValue, setIngestValue] = useState("");
  const [isIngesting, setIsIngesting] = useState(false);

  const handleIngest = async () => {
    if (!ingestValue.trim()) return;
    setIsIngesting(true);
    try {
      const client = getPlantClient();
      const res = await client.ingest(ingestValue.trim());
      if (res.ok) {
        setIngestValue("");
        setShowIngest(false);
      } else {
        alert("Ingest failed: " + (res.error || "Unknown error"));
      }
    } catch (e) {
      console.error("Ingest failed", e);
    } finally {
      setTimeout(() => setIsIngesting(false), 3000);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-20 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="font-mono text-xs tracking-[0.3em]">DAMA DEV</span>
          </div>
          <span className="text-muted-foreground/40">/</span>
          <h1 className="font-serif text-xl text-foreground">Plant</h1>

          <nav className="ml-6 flex items-center gap-1">
            {tabs.map((t) => {
              const active = t.exact ? path === t.to : path.startsWith(t.to);
              return (
                <Link
                  key={t.to}
                  to={t.to}
                  className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors ${
                    active
                      ? "bg-secondary text-foreground"
                      : "text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
                  }`}
                >
                  <t.icon className="h-3.5 w-3.5" strokeWidth={1.75} />
                  {t.label}
                </Link>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-3">
            {showIngest ? (
              <div className="flex items-center gap-1 animate-in slide-in-from-right-2">
                <input
                  autoFocus
                  disabled={isIngesting}
                  value={ingestValue}
                  onChange={(e) => setIngestValue(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleIngest()}
                  placeholder="Paste URL"
                  className="h-8 w-48 rounded-md border border-primary/50 bg-card px-2 font-mono text-xs text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
                />
                <button
                  onClick={handleIngest}
                  disabled={isIngesting}
                  className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:bg-muted"
                >
                  {isIngesting ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <Send className="h-3.5 w-3.5" />
                  )}
                </button>
                <button
                  onClick={() => setShowIngest(false)}
                  disabled={isIngesting}
                  className="flex h-8 w-8 items-center justify-center rounded-md border border-border hover:bg-secondary"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowIngest(true)}
                className="flex h-8 items-center gap-1.5 rounded-md bg-foreground px-3 font-mono text-[10px] uppercase tracking-widest text-background hover:bg-foreground/90 transition-colors"
              >
                {isIngesting ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Plus className="h-3 w-3" />
                )}
                Ingest
              </button>
            )}

            <button
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              className="rounded-md border border-border p-1.5 text-muted-foreground hover:text-foreground"
              aria-label="Toggle theme"
            >
              {theme === "dark" ? (
                <Sun className="h-4 w-4" strokeWidth={1.5} />
              ) : (
                <Moon className="h-4 w-4" strokeWidth={1.5} />
              )}
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
