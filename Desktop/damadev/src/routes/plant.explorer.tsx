import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Database, FolderTree, Terminal, Zap, User, FileText, Search, ImageIcon, ChevronRight, ChevronDown } from "lucide-react";

export const Route = createFileRoute("/plant/explorer")({
  component: DataExplorer,
});

type StoreTab = 'damahdb' | 'damabuffer' | 'damaprompts' | 'damasupabase' | 'damalance' | 'damaevents';

function DataExplorer() {
  const [activeTab, setActiveTab] = useState<StoreTab>('damahdb');

  return (
    <div className="flex flex-col gap-6">
      <header className="flex justify-between items-center">
        <div>
          <h2 className="font-serif text-2xl">Data Explorer</h2>
          <p className="text-sm text-muted-foreground">Authoritative view of all Dama project stores.</p>
        </div>
      </header>

      <div className="flex gap-1 overflow-x-auto pb-2 border-b border-border">
        <StoreNavItem id="damahdb" label="Warehouse" icon={Database} active={activeTab === 'damahdb'} onClick={setActiveTab} />
        <StoreNavItem id="damabuffer" label="Buffer" icon={FileText} active={activeTab === 'damabuffer'} onClick={setActiveTab} />
        <StoreNavItem id="damaprompts" label="Prompts" icon={Terminal} active={activeTab === 'damaprompts'} onClick={setActiveTab} />
        <StoreNavItem id="damasupabase" label="Supabase" icon={User} active={activeTab === 'damasupabase'} onClick={setActiveTab} />
        <StoreNavItem id="damalance" label="Lance VDB" icon={Search} active={activeTab === 'damalance'} onClick={setActiveTab} />
        <StoreNavItem id="damaevents" label="Events" icon={Zap} active={activeTab === 'damaevents'} onClick={setActiveTab} />
      </div>

      <div className="min-h-[500px]">
        {activeTab === 'damahdb' && <HdbExplorer />}
        {activeTab === 'damabuffer' && <BufferExplorer />}
        {activeTab === 'damaprompts' && <PromptExplorer />}
        {activeTab === 'damasupabase' && <SupabaseExplorer />}
        {activeTab === 'damalance' && <LanceExplorer />}
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

// --- TAB: damahdb (Warehouse) ---
function HdbExplorer() {
  const [expanded, setExpanded] = useState<string[]>(['AN', 'AN.Book8']);

  const toggle = (id: string) => {
    setExpanded(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in duration-500">
      <div className="md:col-span-1 rounded-xl border border-border bg-card p-4 space-y-2">
        <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2 mb-4">
          <FolderTree size={14} /> Hierarchy
        </h3>
        <div className="space-y-1 font-mono text-sm">
          <TreeItem id="AN" label="AN (Anguttara Nikaya)" depth={0} expanded={expanded} onToggle={toggle}>
             <TreeItem id="AN.Book8" label="Book 08" depth={1} expanded={expanded} onToggle={toggle}>
                <div className="flex items-center gap-2 p-1.5 pl-10 bg-primary/10 rounded-md text-primary cursor-pointer border border-primary/20">
                  <FileText size={14} /> 8.2.18 (Sealed)
                </div>
                <div className="flex items-center gap-2 p-1.5 pl-10 hover:bg-secondary/40 rounded-md cursor-pointer transition-colors">
                  <FileText size={14} /> 8.2.15 (Validated)
                </div>
             </TreeItem>
             <TreeItem id="AN.Book1" label="Book 01" depth={1} expanded={expanded} onToggle={toggle} />
          </TreeItem>
          <TreeItem id="SN" label="SN (Samyutta Nikaya)" depth={0} expanded={expanded} onToggle={toggle} />
        </div>
      </div>
      <div className="md:col-span-2 space-y-6">
        <div className="rounded-xl border border-border bg-card overflow-hidden">
          <div className="bg-secondary/30 px-4 py-2 border-b border-border flex justify-between items-center">
            <span className="text-xs font-mono">gs://damahdb-dama-492316/.../8.2.18.json</span>
            <div className="flex gap-2">
               <span className="bg-emerald-500/10 text-emerald-500 px-2 py-0.5 rounded text-[10px] font-bold">SEALED</span>
            </div>
          </div>
          <pre className="p-4 text-[11px] overflow-auto h-[400px] leading-relaxed">
{`{
  "sutta_id": "8.2.18",
  "sutta_name_en": "Binding",
  "content": {
    "text": "monks a man enslaves a woman in 8 ways...",
    "translation_ja": "比丘たちよ、男は8つの方法で..."
  },
  "audio": {
    "url": "gs://damahdb-492316/audio/072_AN_8C.mp3",
    "duration_s": 134.76
  },
  "visuals": {
    "manga_panels": [
      {
        "id": "panel_842",
        "url": "gs://...",
        "caption": "Shadowed by the finery of dress..."
      }
    ]
  },
  "metadata": {
    "pipeline_version": "2.3-philosophical",
    "prompt_id": "gs://damaprompts/segmentation/v3.json"
  }
}`}
          </pre>
        </div>
      </div>
    </div>
  );
}

function TreeItem({ id, label, depth, expanded, onToggle, children }: { id: string, label: string, depth: number, expanded: string[], onToggle: (id: string) => void, children?: React.ReactNode }) {
  const isExpanded = expanded.includes(id);
  const paddingLeft = `${depth * 20 + 8}px`;
  return (
    <div>
      <div
        onClick={() => onToggle(id)}
        className="flex items-center gap-2 p-1.5 hover:bg-secondary/40 rounded-md cursor-pointer transition-colors"
        style={{ paddingLeft }}
      >
        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {label}
      </div>
      {isExpanded && children}
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
  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        <table className="w-full text-sm text-left">
          <thead className="bg-secondary/30 text-muted-foreground text-[10px] font-bold uppercase">
            <tr>
              <th className="px-4 py-3">Panel ID</th>
              <th className="px-4 py-3">Preview</th>
              <th className="px-4 py-3">Top Sutta Match</th>
              <th className="px-4 py-3">Similarity</th>
              <th className="px-4 py-3">Embedding</th>
            </tr>
          </thead>
          <tbody className="divide-y border-border">
            <tr className="hover:bg-secondary/20">
              <td className="px-4 py-4 font-mono text-xs text-muted-foreground">buddha_v02_p842</td>
              <td className="px-4 py-4">
                 <div className="w-16 h-12 bg-muted rounded border border-border flex items-center justify-center">
                    <ImageIcon size={16} className="text-muted-foreground/40" />
                 </div>
              </td>
              <td className="px-4 py-4">
                 <div className="font-medium text-primary">AN 8.2.18</div>
                 <div className="text-[10px] text-muted-foreground italic truncate max-w-[200px]">"Man enslaves woman in 8 ways..."</div>
              </td>
              <td className="px-4 py-4 font-mono text-emerald-500 text-xs">0.9842</td>
              <td className="px-4 py-4"><span className="text-[10px] bg-secondary px-1.5 py-0.5 rounded text-muted-foreground">Vector [1536]</span></td>
            </tr>
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
  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden animate-in fade-in duration-500 h-[500px] flex flex-col font-mono text-[11px]">
       <div className="p-3 border-b border-border bg-secondary/20 text-muted-foreground flex items-center gap-2">
          <Terminal size={14} /> pipeline.sqlite3 :: system_events
       </div>
       <div className="flex-1 overflow-auto p-4 space-y-1 bg-black/5 dark:bg-black/20">
          <p className="text-muted-foreground">[2024-05-20 01:45:12] <span className="text-blue-500">INFO</span>: system.init - Registered store damahdb</p>
          <p className="text-muted-foreground">[2024-05-20 01:45:30] <span className="text-blue-500">INFO</span>: store.seed - Uploaded gold standard sutta 8.2.18</p>
          <p className="text-muted-foreground">[2024-05-20 01:46:05] <span className="text-emerald-500">SUCCESS</span>: pipeline.live - All buckets verified</p>
          <p className="animate-pulse">[2024-05-20 01:50:59] <span className="text-primary font-bold">READY</span>: Listening for worker events...</p>
       </div>
    </div>
  );
}
