import { createFileRoute } from "@tanstack/react-router";
import * as React from "react";
import { useState, useEffect } from "react";
import {
  Database,
  FolderTree,
  Terminal,
  Zap,
  User,
  FileText,
  Search,
  ImageIcon,
  ChevronRight,
  ChevronDown,
  Tag,
  CheckCircle2,
  Settings2,
  Play,
  X
} from "lucide-react";

export const Route = createFileRoute("/plant/explorer")({
  component: DataExplorer,
});

type StoreTab = 'damahdb' | 'damabuffer' | 'damaprompts' | 'damasupabase' | 'damalance' | 'damaevents' | 'manga';

function DataExplorer() {
  const [activeTab, setActiveTab] = useState<StoreTab>('damaevents');

  return (
    <div className="flex flex-col gap-6">
      <header className="flex justify-between items-center">
        <div>
          <h2 className="font-serif text-2xl">Data Explorer</h2>
          <p className="text-sm text-muted-foreground">Authoritative view of all Dama project stores.</p>
        </div>
      </header>

      <div className="flex gap-1 overflow-x-auto pb-2 border-b border-border">
        <StoreNavItem id="damaevents" label="damaevents" icon={Zap} active={activeTab === 'damaevents'} onClick={setActiveTab} />
        <StoreNavItem id="damahdb" label="damahdb" icon={Database} active={activeTab === 'damahdb'} onClick={setActiveTab} />
        <StoreNavItem id="damabuffer" label="damabuffer" icon={FileText} active={activeTab === 'damabuffer'} onClick={setActiveTab} />
        <StoreNavItem id="damaprompts" label="damaprompts" icon={Terminal} active={activeTab === 'damaprompts'} onClick={setActiveTab} />
        <StoreNavItem id="damasupabase" label="damasupabase" icon={User} active={activeTab === 'damasupabase'} onClick={setActiveTab} />
        <StoreNavItem id="damalance" label="damalance" icon={Search} active={activeTab === 'damalance'} onClick={setActiveTab} />
        <StoreNavItem id="manga" label="manga" icon={ImageIcon} active={activeTab === 'manga'} onClick={setActiveTab} />
      </div>

      <div className="min-h-[500px]">
        {activeTab === 'damahdb' && <HdbExplorer />}
        {activeTab === 'damabuffer' && <BufferExplorer />}
        {activeTab === 'damaprompts' && <PromptExplorer />}
        {activeTab === 'damasupabase' && <SupabaseExplorer />}
        {activeTab === 'damalance' && <LanceExplorer />}
        {activeTab === 'manga' && <MangaExplorer />}
        {activeTab === 'damaevents' && <EventsExplorer />}
      </div>
    </div>
  );
}

function StoreNavItem({ id, label, icon: Icon, active, onClick }: { id: StoreTab, label: string, icon: any, active: boolean, onClick: (id: StoreTab) => void }) {
  return (
    <button
      onClick={() => onClick(id)}
      className={`flex items-center gap-2 px-4 py-2 rounded-t-lg text-sm transition-colors ${
        active ? "bg-secondary text-primary font-medium" : "text-muted-foreground hover:bg-secondary/40"
      }`}
    >
      <Icon size={16} />
      {label}
    </button>
  );
}

// --- SHARED: Pipeline Control ---
function PipelineControl({ selectedFile, content, activeStage, handleReplay }: { selectedFile: string | null, content: string, activeStage: string | null, handleReplay: (stages?: string[]) => Promise<void> }) {
  return (
    <div className="space-y-2">
      <h4 className="text-[11px] font-bold uppercase tracking-[0.2em] text-muted-foreground mb-6">Pipeline Control</h4>

      <button
        onClick={() => handleReplay()}
        className={`w-full group flex items-center justify-between p-4 rounded-xl border transition-all duration-300 ${
          !activeStage ? 'bg-amber-50 border-amber-200 text-amber-900 shadow-sm' : 'bg-secondary/20 border-border text-muted-foreground'
        }`}
      >
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${!activeStage ? 'bg-amber-500 text-white' : 'bg-muted text-muted-foreground'}`}>
            <Play size={14} fill="currentColor" />
          </div>
          <div className="text-left">
            <p className="text-sm font-bold">Execute Full Pipeline</p>
            <p className="text-[10px] opacity-70">Run all stages sequentially</p>
          </div>
        </div>
        <ChevronRight size={16} className={!activeStage ? 'text-amber-500' : 'text-muted-foreground'} />
      </button>

      <div className="py-4 flex items-center gap-4">
        <div className="h-px flex-1 bg-border/50"></div>
        <span className="text-[9px] font-bold text-muted-foreground uppercase tracking-widest">Individual Stages</span>
        <div className="h-px flex-1 bg-border/50"></div>
      </div>

      <div className="grid gap-2">
        {[
          { id: 'align', label: '1. Align Split', desc: 'Segment audio & text' },
          { id: 'mcq', label: '2. Gen MCQ', desc: 'Commentary & quiz generation' },
          { id: 'translate', label: '3. Translate', desc: 'Japanese localization' },
          { id: 'judge', label: '4. QC Audit', desc: 'LLM Quality Control' },
          { id: 'dub', label: '5. Dubbing', desc: 'Voice synthesis' },
          { id: 'embed', label: '6. VDB Embed', desc: 'Vector database indexing' },
          { id: 'seal', label: '7. Seal to Cloud', desc: 'Finalize & Upload' }
        ].map((stage) => {
          const isActive = activeStage === stage.id;
          return (
            <button
              key={stage.id}
              onClick={() => handleReplay([stage.id])}
              className={`w-full flex items-center justify-between p-3 rounded-lg border transition-all duration-200 ${
                isActive
                  ? 'bg-[#00A36C] border-[#00A36C] text-white shadow-lg shadow-[#00A36C]/20 animate-pulse scale-[1.02]'
                  : 'bg-card border-border hover:border-primary/30 hover:bg-secondary/10 text-foreground'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`text-[10px] font-bold w-5 h-5 flex items-center justify-center rounded-full ${isActive ? 'bg-white/20' : 'bg-secondary text-muted-foreground'}`}>
                  {stage.id === 'seal' ? '✓' : stage.label.split('.')[0]}
                </div>
                <div className="text-left">
                  <p className="text-[12px] font-bold">{stage.label.split('. ')[1]}</p>
                  <p className={`text-[9px] ${isActive ? 'text-white/80' : 'text-muted-foreground'}`}>{stage.desc}</p>
                </div>
              </div>
              {isActive && <div className="flex gap-1 pr-2">
                <div className="w-1 h-1 bg-white rounded-full animate-bounce"></div>
                <div className="w-1 h-1 bg-white rounded-full animate-bounce [animation-delay:0.2s]"></div>
                <div className="w-1 h-1 bg-white rounded-full animate-bounce [animation-delay:0.4s]"></div>
              </div>}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// --- TAB: damahdb (Warehouse) ---
function HdbExplorer() {
  const [files, setFiles] = React.useState<any[]>([]);
  const [selectedFile, setSelectedFile] = React.useState<string | null>(null);
  const [content, setContent] = React.useState<string>("");
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    fetch("/api/codex4").then(r => r.json()).then(setFiles);
  }, []);

  const handleSelect = async (filename: string) => {
    setSelectedFile(filename);
    setLoading(true);
    try {
      const res = await fetch(`/api/codex4?file=${encodeURIComponent(filename)}`);
      const data = await res.text();
      setContent(data);
    } finally {
      setLoading(false);
    }
  };

  const [activeStage, setActiveStage] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!selectedFile) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch("/api/events");
        const events = await res.json();
        // Find latest event for this file's sutta
        try {
          const contentObj = JSON.parse(content);
          const suttaId = contentObj.sutta_id;
          const relevantEvent = events.find((e: any) => e.vid === suttaId || contentObj.vid === e.vid);
          if (relevantEvent && relevantEvent.status === 'START') {
            setActiveStage(relevantEvent.stage);
          } else if (relevantEvent && relevantEvent.status === 'DONE') {
            // If it's DONE, we check if it was the last stage or wait for next START
            // For simplicity, if latest is DONE, clear active stage
             setActiveStage(null);
          }
        } catch(e) {}
      } catch (e) {}
    }, 3000);
    return () => clearInterval(interval);
  }, [selectedFile, content]);

  const handleReplay = async (stages?: string[]) => {
    if (!selectedFile) return;
    try {
      const contentObj = JSON.parse(content);
      const suttaId = contentObj.sutta_id;
      if (!suttaId) return;

      // Always include judge if specific stages are picked
      const finalStages = stages && !stages.includes('judge') ? [...stages, 'judge'] : stages;

      const res = await fetch("/work-api/replay", {
        method: "POST",
        body: JSON.stringify({ sutta_id: suttaId, stages: finalStages }),
        headers: { "Content-Type": "application/json" },
      });
      const data = await res.json();
      if (data.ok) {
        alert(`Replay started for ${suttaId}${stages ? ` (${stages.join(", ")})` : ""}. Watch the 'damaevents' tab for progress.`);
      } else {
        alert(`Failed to start replay: ${data.error}`);
      }
    } catch (e) {
      console.error(e);
      alert("Error parsing file for replay.");
    }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in duration-500">
      <div className="md:col-span-1 rounded-xl border border-border bg-card p-4 space-y-2 max-h-[600px] overflow-y-auto">
        <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2 mb-4">
          <FolderTree size={14} /> Codex4 Files
        </h3>
        <div className="space-y-1 font-mono text-sm">
          {files.map(f => (
            <div
              key={f.name}
              onClick={() => handleSelect(f.name)}
              className={`flex items-center gap-2 p-1.5 rounded-md cursor-pointer transition-colors ${selectedFile === f.name ? "bg-primary/10 text-primary border border-primary/20" : "hover:bg-secondary/40"}`}
            >
              <FileText size={14} /> {f.id}
            </div>
          ))}
          {files.length === 0 && <div className="text-xs text-muted-foreground p-4">No files found in codex4.</div>}
        </div>
      </div>
      <div className="md:col-span-2 space-y-6">
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="bg-secondary/30 px-4 py-2 border-b border-border flex justify-between items-center h-12">
            <span className="text-xs font-mono">{selectedFile || "Select a file to preview"}</span>
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 divide-x divide-border relative">
            <pre className="p-4 text-[11px] overflow-auto h-[600px] leading-relaxed whitespace-pre-wrap break-words">
              {loading ? "Loading..." : content || "{}"}
            </pre>
            <div className="p-8 h-[600px] overflow-auto bg-background relative">
               <PipelineControl
                  selectedFile={selectedFile}
                  content={content}
                  activeStage={activeStage}
                  handleReplay={handleReplay}
               />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- TAB: manga (Bridge) ---
function MangaExplorer() {
  const [book, setBook] = useState("All Books");
  const [volume, setVolume] = useState("v01");
  const [limit, setLimit] = useState(100);
  const [isRunning, setIsRunning] = useState(false);
  const [panels, setPanels] = useState<any[]>([]);
  const [selectedSutta, setSelectedSutta] = useState<string | null>(null);
  const [suttas, setSuttas] = useState<any[]>([]);
  const [lanceSuttaIds, setLanceSuttaIds] = useState<string[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showValidatedOnly, setShowValidatedOnly] = useState(false);
  const [counts, setCounts] = useState({ lance: 0, gcs: 58, local: 17 });

  // New states for tagging and detailed view
  const [taggedSuttaIds, setTaggedSuttaIds] = useState<Set<string>>(new Set());
  const [selectedPanel, setSelectedPanel] = useState<any>(null);

  // Pipeline State for selected Sutta
  const [content, setContent] = useState<string>("");
  const [activeStage, setActiveStage] = React.useState<string | null>(null);

  const handleTagPanel = async (suttaId: string, panel: any) => {
    if (window.confirm(`Confirm: Link Sutta ${suttaId} to Panel ${panel.id}?`)) {
      try {
        // 1. Update Codex JSON (Sutta -> Panel mapping)
        await fetch("/api/codex4", {
          method: "POST",
          body: JSON.stringify({
            sutta_id: suttaId,
            updates: {
              tagged: true,
              manga_panel: panel.id,
              manga_volume: panel.volume
            }
          }),
          headers: { "Content-Type": "application/json" },
        });

        // 2. Update LanceDB (Panel -> Sutta mapping)
        await fetch("/api/lance", {
          method: "PUT",
          body: JSON.stringify({
            sutta_id: suttaId,
            panel_id: panel.id,
            volume: panel.volume
          }),
          headers: { "Content-Type": "application/json" },
        });

        setTaggedSuttaIds(prev => new Set(prev).add(suttaId));
        // Update local panels state to show the green border immediately
        setPanels(prev => prev.map(p =>
          (p.id === panel.id && p.volume === panel.volume)
            ? { ...p, sutta_id: suttaId }
            : p
        ));
        setSelectedPanel(null);
        alert(`Successfully linked ${suttaId} to ${panel.id} in LanceDB.`);
      } catch (e) {
        console.error(e);
        alert("Failed to persist tag to LanceDB.");
      }
    }
  };

  // Fetch real suttas from Codex4
  useEffect(() => {
    const loadData = async () => {
      // 1. Load files from Codex4
      const res = await fetch("/api/codex4");
      const files = await res.json();
      setSuttas(files);

      // 2. Load indexed IDs from LanceDB
      try {
        const lRes = await fetch("/api/lance", {
          method: "POST",
          body: JSON.stringify({ action: "list_suttas" }),
          headers: { "Content-Type": "application/json" }
        });
        const lIds = await lRes.json();
        setLanceSuttaIds(lIds);
        setCounts(prev => ({ ...prev, lance: lIds.length }));
      } catch (e) { console.error(e); }

      const tagged = new Set(files.filter((s: any) => s.tagged).map((s: any) => s.id));
      setTaggedSuttaIds(tagged);

      if (files.length > 0 && !selectedSutta) {
        const firstValid = files.find((s: any) => s.valid) || files[0];
        setSelectedSutta(firstValid.id);
      }
    };

    loadData();
  }, []);

  // Fetch full JSON content when sutta changes for the pipeline control
  useEffect(() => {
    if (!selectedSutta) return;
    // We need the filename which usually starts with "AN "
    const filename = `AN ${selectedSutta}.json`;
    fetch(`/api/codex4?file=${encodeURIComponent(filename)}`)
      .then(res => res.text())
      .then(setContent)
      .catch(console.error);
  }, [selectedSutta]);

  // Event polling for active stage (shared logic)
  useEffect(() => {
    if (!selectedSutta) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch("/api/events");
        const events = await res.json();
        const relevantEvent = events.find((e: any) => e.vid === selectedSutta);
        if (relevantEvent && relevantEvent.status === 'START') {
          setActiveStage(relevantEvent.stage);
        } else if (relevantEvent && relevantEvent.status === 'DONE') {
           setActiveStage(null);
        }
      } catch (e) {}
    }, 3000);
    return () => clearInterval(interval);
  }, [selectedSutta]);

  // Search for matching panels when sutta changes
  useEffect(() => {
    if (!selectedSutta) return;
    setIsSearching(true);
    fetch("/api/lance", {
      method: "POST",
      body: JSON.stringify({ sutta_id: selectedSutta }),
    })
      .then(r => r.json())
      .then(data => {
        setPanels(Array.isArray(data) ? data : []);
        setIsSearching(false);
      })
      .catch(e => {
        console.error(e);
        setIsSearching(false);
      });
  }, [selectedSutta]);

  const handleReplay = async (stages?: string[]) => {
    if (!selectedSutta) return;
    try {
      const finalStages = stages && !stages.includes('judge') ? [...stages, 'judge'] : stages;
      const res = await fetch("/work-api/replay", {
        method: "POST",
        body: JSON.stringify({ sutta_id: selectedSutta, stages: finalStages }),
        headers: { "Content-Type": "application/json" },
      });
      const data = await res.json();
      if (data.ok) {
        alert(`Replay started for ${selectedSutta}.`);
      }
    } catch (e) { console.error(e); }
  };

  const runSeal = async () => {
    setIsRunning(true);
    try {
      const fullVolume = `${volume}`;
      const res = await fetch("/work-api/manga-process", {
        method: "POST",
        body: JSON.stringify({ volume: fullVolume, limit }),
        headers: { "Content-Type": "application/json" },
      });
      const data = await res.json();
      alert(data.message);
    } catch (e) {
      console.error(e);
    } finally {
      setTimeout(() => setIsRunning(false), 2000);
    }
  };

  const getBookName = (suttaId: string) => {
    if (!suttaId) return "Unknown Book";
    const match = suttaId.match(/^(\d+)\./);
    if (!match) return "Unknown Book";
    const num = parseInt(match[1]);
    const names = ["", "Book of Ones", "Book of Twos", "Book of Threes", "Book of Fours", "Book of Fives", "Book of Sixes", "Book of Sevens", "Book of Eights", "Book of Nines", "Book of Tens", "Book of Elevens"];
    return names[num] || `Book ${num}`;
  };

  const filteredSuttas = suttas.filter(s => {
    const passValidated = !showValidatedOnly || s.valid;
    const passBook = book === "All Books" || getBookName(s.id) === book;
    return passValidated && passBook;
  });

  const untaggedSuttas = filteredSuttas.filter(s => !taggedSuttaIds.has(s.id));
  const taggedSuttas = filteredSuttas.filter(s => taggedSuttaIds.has(s.id));

  const getPanelScore = (panel: any) => {
    const dist = panel._distance || 0;
    return Math.round((1 / (1 + dist)) * 100);
  };
  const sortedPanels = [...panels].sort((a, b) => getPanelScore(b) - getPanelScore(a));

  return (
    <div className="flex h-[750px] flex-col space-y-4 animate-in fade-in duration-500">
      <div className="flex items-center justify-between border-b border-border bg-card/50 p-3 rounded-t-xl">
        <div className="flex items-center gap-4">
          <div className="flex h-8 items-center gap-2 rounded-md border border-border bg-background px-2">
            <span className="text-[10px] font-bold uppercase text-muted-foreground">Book:</span>
            <select
              value={book}
              onChange={(e) => setBook(e.target.value)}
              className="bg-transparent text-sm font-bold focus:outline-none"
            >
              <option value="All Books">All Books</option>
              {Array.from(new Set(suttas.map(s => getBookName(s.id))))
                .filter(b => b !== "Unknown Book")
                .sort((a, b) => {
                  const getNum = (s: string) => {
                    const m = s.match(/\d+/);
                    return m ? parseInt(m[0]) : 99;
                  };
                  return getNum(a) - getNum(b);
                })
                .map(b => (
                  <option key={b} value={b}>{b}</option>
                ))}
            </select>
          </div>
        </div>

        <div className="flex items-center gap-3">
        </div>
      </div>

      <div className="grid flex-1 grid-cols-[250px_1fr_280px] gap-4 overflow-hidden pb-4">
        {/* Left: Sutta List */}
        <div className="flex flex-col gap-4 overflow-y-auto rounded-md border border-border bg-card p-4">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Target Sutta</h3>
              <button
                onClick={() => setShowValidatedOnly(!showValidatedOnly)}
                className={`text-[9px] px-2 py-0.5 rounded border transition-colors ${showValidatedOnly ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-600 font-bold' : 'bg-secondary border-border text-muted-foreground'}`}
              >
                {showValidatedOnly ? 'Validated' : 'All Files'}
              </button>
            </div>
            <div className="flex flex-col gap-1">
              {untaggedSuttas.map(s => (
                <button
                  key={s.id}
                  onClick={() => setSelectedSutta(s.id)}
                  className={`flex items-center justify-between rounded-md px-3 py-2 text-left text-sm transition-colors border ${
                    selectedSutta === s.id
                      ? "bg-primary/10 text-primary border-primary/20 shadow-inner"
                      : "hover:bg-secondary border border-transparent"
                  }`}
                >
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <span className={`font-bold ${s.valid ? 'text-foreground' : 'text-muted-foreground'}`}>{s.id}</span>
                      {lanceSuttaIds.includes(s.id) && (
                        <span className="text-[7px] bg-primary/20 text-primary px-1 rounded font-bold uppercase tracking-tighter">VDB</span>
                      )}
                      {s.score !== undefined && (
                        <span className={`text-[9px] px-1 rounded-sm font-mono text-white ${
                          s.valid ? 'bg-[#00A36C]' : 'bg-status-err'
                        }`}>
                          {s.score}/10
                        </span>
                      )}
                    </div>
                    <span className="text-[10px] opacity-60 truncate max-w-[150px]">{s.title || "No Title"}</span>
                  </div>
                </button>
              ))}

              {taggedSuttas.length > 0 && (
                <>
                  <div className="my-4 border-t border-border pt-4">
                    <h3 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-2">Tagged</h3>
                  </div>
                  {taggedSuttas.map(s => (
                    <button
                      key={s.id}
                      onClick={() => setSelectedSutta(s.id)}
                      className={`flex items-center justify-between rounded-md px-3 py-2 text-left text-sm transition-colors border ${
                        selectedSutta === s.id
                          ? "bg-primary/5 text-primary border-primary/10"
                          : "bg-secondary/20 border-transparent opacity-60"
                      }`}
                    >
                      <div className="flex flex-col gap-0.5">
                        <span className="font-bold">{s.id}</span>
                        <span className="text-[10px] truncate max-w-[150px]">{s.title || "No Title"}</span>
                      </div>
                      <CheckCircle2 className="h-3 w-3 text-[#00A36C]" />
                    </button>
                  ))}
                </>
              )}
            </div>
          </div>
        </div>

        {/* Middle: Panel Grid */}
        <div className="flex flex-col gap-4 overflow-y-auto rounded-md border border-border bg-card p-6 relative">
          <div className="grid grid-cols-2 gap-6 lg:grid-cols-3">
            {isSearching ? (
              <div className="col-span-full py-20 text-center font-mono text-sm text-muted-foreground animate-pulse">
                Searching Vector Database for matches...
              </div>
            ) : sortedPanels.length === 0 ? (
              <div className="col-span-full py-20 text-center font-mono text-sm text-muted-foreground">
                No matches found.
              </div>
            ) : sortedPanels.map((panel, i) => (
              <div
                key={i}
                onClick={() => setSelectedPanel(panel)}
                className={`group relative aspect-[3/4] overflow-hidden rounded-xl border transition-all hover:shadow-xl cursor-pointer ${
                  panel.sutta_id === selectedSutta
                    ? "border-[#00A36C] border-4 ring-4 ring-[#00A36C]/20"
                    : "border-border hover:ring-2 hover:ring-primary"
                } bg-secondary/10`}
              >
                {panel.volume && panel.id ? (
                  <img
                    src={`/api/manga/image/${panel.volume}/${panel.id}`}
                    alt={panel.id}
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                    loading="lazy"
                  />
                ) : (
                  <div className="flex h-full p-6 items-center justify-center text-center text-[10px] text-muted-foreground italic leading-relaxed">
                    {panel.text?.slice(0, 150)}...
                  </div>
                )}

                <div className="absolute inset-0 flex flex-col justify-end bg-gradient-to-t from-black/90 via-black/20 to-transparent p-4 opacity-0 transition-opacity group-hover:opacity-100">
                  <p className="mb-4 text-[11px] text-white leading-relaxed line-clamp-4 italic border-l-2 border-primary/50 pl-3">
                    {panel.text}
                  </p>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTagPanel(selectedSutta!, panel);
                    }}
                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-2 text-[11px] font-bold uppercase text-white hover:bg-primary/90 transition-transform hover:scale-[1.02]"
                  >
                    <Tag className="h-3 w-3" /> Tag Sutta
                  </button>
                </div>

                  <div className="absolute top-3 right-3 flex items-center gap-2">
                    {panel.sutta_id === selectedSutta && (
                      <div className="rounded-full bg-[#00A36C] p-1 text-white shadow-lg">
                        <CheckCircle2 size={12} />
                      </div>
                    )}
                    <div className="rounded-full bg-black/60 backdrop-blur-md px-2 py-1 text-[9px] font-bold text-white tracking-tighter shadow-sm">
                      {getPanelScore(panel)}% Match
                    </div>
                  </div>
                </div>
            ))}
          </div>
        </div>

        {/* Right: Sutta Text Panel */}
        <div className="flex flex-col gap-4 overflow-y-auto rounded-md border border-border bg-card p-6 shadow-sm">
           <h3 className="text-[11px] font-bold uppercase tracking-[0.2em] text-primary mb-4 flex items-center gap-2">
             <FileText size={14} /> Sutta Content
           </h3>
           <div className="flex-1 space-y-6">
              <div>
                 <p className="text-[10px] font-bold text-muted-foreground uppercase mb-2">Pali Title</p>
                 <p className="text-sm font-serif italic">
                    {(() => {
                        try { return JSON.parse(content).sutta_name_pali || "---"; } catch { return "---"; }
                    })()}
                 </p>
              </div>

              <div className="h-px bg-border/50"></div>

              <div>
                 <p className="text-[10px] font-bold text-muted-foreground uppercase mb-2">Original Text</p>
                 <div className="text-sm font-serif leading-relaxed text-foreground/90 whitespace-pre-wrap max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                    {(() => {
                        try {
                          const obj = JSON.parse(content);
                          return obj.sutta || "No text content available.";
                        } catch {
                          return "Select a sutta to view content.";
                        }
                    })()}
                 </div>
              </div>

              {(() => {
                try {
                   const obj = JSON.parse(content);
                   if (obj.commentary) {
                      return (
                        <>
                           <div className="h-px bg-border/50"></div>
                           <div>
                              <p className="text-[10px] font-bold text-muted-foreground uppercase mb-2">Teacher's Commentary</p>
                              <div className="text-[13px] leading-relaxed text-muted-foreground italic max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                                 {obj.commentary}
                              </div>
                           </div>
                        </>
                      );
                   }
                } catch {}
                return null;
              })()}
           </div>
        </div>
      </div>

      {/* Modal for Panel Detail */}
      {selectedPanel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-background w-full max-w-4xl max-h-[90vh] rounded-2xl border border-border overflow-hidden flex flex-col shadow-2xl">
            <div className="flex items-center justify-between p-4 border-b border-border bg-secondary/20">
              <h3 className="font-serif text-lg font-bold">Panel Detail — {getPanelScore(selectedPanel)}% Match</h3>
              <button onClick={() => setSelectedPanel(null)} className="p-2 hover:bg-secondary rounded-full transition-colors">
                 <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-4">
                  <div className="aspect-[3/4] rounded-xl overflow-hidden border border-border bg-secondary/10">
                    <img
                      src={`/api/manga/image/${selectedPanel.volume}/${selectedPanel.id}`}
                      alt={selectedPanel.id}
                      className="w-full h-full object-contain"
                    />
                  </div>
                  <div className="p-4 rounded-xl bg-secondary/30 border border-border">
                    <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground mb-2">Panel Description</p>
                    <p className="text-sm italic leading-relaxed text-foreground/80">{selectedPanel.text}</p>
                  </div>

                  <div className="p-4 rounded-xl bg-primary/5 border border-primary/20">
                    <p className="text-xs font-bold uppercase tracking-widest text-primary mb-2">Semantic Reasoning</p>
                    <p className="text-sm leading-relaxed text-foreground/80">
                      Matches the conceptual themes of <span className="font-bold underline text-primary">impermanence</span> and <span className="font-bold underline text-primary">mental resolve</span> found in {selectedSutta}.
                      The visual composition emphasizes the {selectedPanel.text?.includes('action') ? 'dynamic nature' : 'internal conflict'} described in the teaching.
                    </p>
                  </div>
                </div>
                <div className="space-y-6">
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-widest text-primary mb-3">Matching Sutta: {selectedSutta}</h4>
                    <div className="max-h-[400px] overflow-y-auto p-4 rounded-xl bg-background border border-border font-serif text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap">
                      {(() => {
                        try {
                          const obj = JSON.parse(content);
                          return obj.sutta || "No text available";
                        } catch (e) {
                          return "Loading sutta text...";
                        }
                      })()}
                    </div>
                  </div>

                  <button
                    onClick={() => handleTagPanel(selectedSutta!, selectedPanel)}
                    className="w-full flex items-center justify-center gap-2 rounded-xl bg-primary py-4 text-sm font-bold uppercase text-white hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
                  >
                    <Tag size={18} /> Confirm & Tag Sutta
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


// --- TAB: damaprompts (Prompts) ---
function PromptExplorer() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-secondary/30 text-muted-foreground text-[10px] font-bold uppercase">
            <tr>
              <th className="px-4 py-3">Workflow</th>
              <th className="px-4 py-3">Latest Version</th>
              <th className="px-4 py-3">Model</th>
              <th className="px-4 py-3">Last Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y border-border">
            <tr className="hover:bg-secondary/20 transition-colors">
              <td className="px-4 py-4 font-medium italic">sutta-segmentation</td>
              <td className="px-4 py-4"><span className="bg-primary/10 text-primary px-2 py-0.5 rounded font-mono">v3.0</span></td>
              <td className="px-4 py-4 font-mono text-xs">qwen2.5:14b</td>
              <td className="px-4 py-4 text-muted-foreground text-xs">2024-05-20</td>
            </tr>
            <tr className="hover:bg-secondary/20 transition-colors">
              <td className="px-4 py-4 font-medium italic">manga-philosophy</td>
              <td className="px-4 py-4"><span className="bg-primary/10 text-primary px-2 py-0.5 rounded font-mono">v2.3</span></td>
              <td className="px-4 py-4 font-mono text-xs">llava + qwen</td>
              <td className="px-4 py-4 text-muted-foreground text-xs">2024-05-18</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
           <h4 className="text-[10px] font-bold uppercase text-muted-foreground px-2">Prompt v2.3</h4>
           <div className="p-4 bg-red-500/5 border border-red-500/10 rounded-lg text-xs leading-relaxed text-muted-foreground line-through decoration-red-500/50">
             Analyze this manga panel. Describe what the character is doing. Use simple language.
           </div>
        </div>
        <div className="space-y-2">
           <h4 className="text-[10px] font-bold uppercase text-primary px-2">Prompt v3.0 (New)</h4>
           <div className="p-4 bg-emerald-500/5 border border-emerald-500/20 rounded-lg text-xs leading-relaxed text-foreground">
             Identify the emotional tension (ambition, grief, peace). Use Evo-cative, compound words. BANNED: "This panel shows".
           </div>
        </div>
      </div>
    </div>
  );
}

// --- TAB: damalance (Lance VDB) ---
function LanceExplorer() {
  const [data, setData] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch("/api/lance").then(r => r.json()).then(d => {
      setData(d);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-secondary/30 text-muted-foreground text-[10px] font-bold uppercase">
            <tr>
              <th className="px-4 py-3">ID</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-4 py-3">Sutta ID</th>
              <th className="px-4 py-3">Text Snippet</th>
            </tr>
          </thead>
          <tbody className="divide-y border-border">
            {loading ? (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-muted-foreground font-mono text-xs">Loading Vector Database...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={4} className="px-4 py-8 text-center text-muted-foreground font-mono text-xs">Database empty. Run 25_embed.py first.</td></tr>
            ) : data.map((row) => (
              <tr key={row.id} className="hover:bg-secondary/20">
                <td className="px-4 py-4 font-mono text-xs text-muted-foreground">{row.id}</td>
                <td className="px-4 py-4">
                   <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${row.type === 'sutta' ? 'bg-primary/10 text-primary' : 'bg-amber-500/10 text-amber-500'}`}>
                     {row.type}
                   </span>
                </td>
                <td className="px-4 py-4 font-medium text-foreground">{row.sutta_id}</td>
                <td className="px-4 py-4 text-[10px] text-muted-foreground italic truncate max-w-[400px]">
                  {row.text}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --- TAB: damasupabase (Mock) ---
function SupabaseExplorer() {
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="rounded-xl border border-border bg-card p-5 space-y-4">
           <h3 className="text-xs font-bold uppercase text-muted-foreground flex items-center gap-2">
             <User size={14} /> Active Profiles
           </h3>
           <div className="space-y-3">
              <div className="flex items-center gap-3">
                 <div className="size-8 rounded-full bg-primary/20 flex items-center justify-center text-[10px] font-bold">JD</div>
                 <div className="text-xs">
                    <div className="font-medium text-foreground">JohnDhamma</div>
                    <div className="text-muted-foreground font-mono text-[10px]">UUID: 4a2b...</div>
                 </div>
              </div>
           </div>
        </div>
        <div className="md:col-span-2 rounded-xl border border-border bg-card overflow-hidden">
          <div className="p-4 border-b border-border bg-secondary/20 flex justify-between items-center">
             <h3 className="text-xs font-bold uppercase text-primary">Live Agent Traces (LangGraph)</h3>
             <span className="text-[10px] font-mono text-muted-foreground">Recent 50</span>
          </div>
          <div className="divide-y divide-border">
             <div className="p-4 hover:bg-secondary/20 transition-colors space-y-2">
                <div className="flex justify-between items-center">
                   <span className="text-xs font-bold">Intent: segmentation_upgrade</span>
                   <span className="text-[10px] text-muted-foreground">2 mins ago</span>
                </div>
                <div className="flex gap-2">
                   {['Planner', 'Parser', 'Validator'].map(step => (
                     <span key={step} className="bg-primary/5 border border-primary/10 px-2 py-0.5 rounded text-[10px] font-medium text-primary flex items-center gap-1">
                        <ChevronRight size={10} /> {step}
                     </span>
                   ))}
                </div>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- TAB: damabuffer (Assets) ---
function BufferExplorer() {
  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden animate-in fade-in duration-500">
       <div className="p-4 border-b border-border bg-secondary/20">
          <h3 className="text-xs font-bold uppercase text-muted-foreground">Unprocessed Assets</h3>
       </div>
       <table className="w-full text-sm text-left">
          <thead className="bg-secondary/10 text-muted-foreground text-[10px] font-bold uppercase">
            <tr>
              <th className="px-4 py-3">File Path</th>
              <th className="px-4 py-3">Source</th>
              <th className="px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border font-mono text-xs">
            <tr className="hover:bg-secondary/20">
              <td className="px-4 py-3 text-muted-foreground italic truncate max-w-[400px]">gs://damabuffer-492316/raw/transcripts/SUTTA_f6d706b3.en.json3</td>
              <td className="px-4 py-3">YouTube (vid: f6d706b3)</td>
              <td className="px-4 py-3"><span className="text-amber-500">PENDING_LLM</span></td>
            </tr>
          </tbody>
       </table>
    </div>
  );
}

// --- TAB: damaevents (Logs) ---
function EventsExplorer() {
  const [events, setEvents] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch("/api/events").then(r => r.json()).then(d => {
      setEvents(d);
      setLoading(false);
    });
  }, []);

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden animate-in fade-in duration-500 h-[500px] flex flex-col font-mono text-[11px]">
       <div className="p-3 border-b border-border bg-secondary/20 text-muted-foreground flex items-center gap-2">
          <Terminal size={14} /> pipeline.sqlite3 :: events
       </div>
       <div className="flex-1 overflow-auto p-4 space-y-1 bg-black/5 dark:bg-black/20">
          {loading ? (
            <p className="text-muted-foreground">Loading system events...</p>
          ) : events.length === 0 ? (
            <p className="text-muted-foreground italic">No events logged yet. Start the pipeline to see activity.</p>
          ) : events.map((e) => (
            <p key={e.id} className="text-muted-foreground border-b border-border/5 pb-1 mb-1">
              <span className="text-[10px] opacity-50">[{e.timestamp}]</span>{" "}
              <span className={`font-bold ${e.status === 'DONE' ? 'text-emerald-500' : e.status === 'FAIL' ? 'text-status-err' : 'text-primary'}`}>
                {e.stage}.{e.status}
              </span>:{" "}
              <span className="text-foreground/80">{e.vid}</span> - {e.message}
            </p>
          ))}
       </div>
    </div>
  );
}
