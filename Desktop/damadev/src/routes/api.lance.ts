import { createFileRoute } from "@tanstack/react-router";
import { spawnSync } from "node:child_process";
import path from "node:path";

export const Route = createFileRoute("/api/lance")({
  server: {
    handlers: {
      GET: async () => {
        const pythonCommand = process.platform === "win32" ? "python.exe" : "python3";
        // Simple script to list some entries from LanceDB
        const script = `
import lancedb, json, pathlib, warnings
warnings.filterwarnings("ignore")
root = pathlib.Path.cwd()
db_path = root / "data" / "damalance"
if not db_path.exists():
    print(json.dumps([]))
    exit(0)
db = lancedb.connect(str(db_path))
tables = db.table_names()

if "sutta_knowledge" not in tables:
    print(json.dumps([]))
    exit(0)
tbl = db.open_table("sutta_knowledge")
# Just get 20 entries
df = tbl.to_pandas().head(20)
# Exclude vector for size
columns_to_drop = ['vector'] if 'vector' in df.columns else []
records = df.drop(columns=columns_to_drop).to_dict(orient='records')
print(json.dumps(records))
`;

        const result = spawnSync(pythonCommand, ["-c", script], {
          cwd: process.cwd(),
          encoding: "utf8",
          timeout: 10000,
          windowsHide: true,
        });

        if (result.status !== 0) {
          return new Response(JSON.stringify({ error: result.stderr }), {
            status: 500,
            headers: { "Content-Type": "application/json" },
          });
        }

        return new Response(result.stdout, {
          headers: { "Content-Type": "application/json; charset=utf-8" },
        });
      },
      POST: async ({ request }) => {
        const body = await request.json();
        const { sutta_id, action } = body;

        if (action === "list_suttas") {
            const pythonCommand = process.platform === "win32" ? "python.exe" : "python3";
            const script = `
import lancedb, json, pathlib, warnings
warnings.filterwarnings("ignore")
db = lancedb.connect("data/damalance")
if "sutta_knowledge" not in db.table_names():
    print(json.dumps([]))
else:
    tbl = db.open_table("sutta_knowledge")
    ids = sorted(list(set(tbl.to_pandas()["sutta_id"].tolist())))
    print(json.dumps(ids))
`;
            const result = spawnSync(pythonCommand, ["-c", script], { cwd: process.cwd(), encoding: "utf8" });
            return new Response(result.stdout, { headers: { "Content-Type": "application/json" } });
        }

        const { sutta_id: search_id } = body;
        const pythonCommand = process.platform === "win32" ? "python.exe" : "python3";

        const script = `
import lancedb, json, pathlib, os, warnings
import pandas as pd
warnings.filterwarnings("ignore")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print(json.dumps({"error": "sentence-transformers not installed"}))
    exit(0)

root = pathlib.Path.cwd()
db_path = root / "data" / "damalance"
if not db_path.exists():
    print(json.dumps({"error": "Database path not found"}))
    exit(0)

db = lancedb.connect(str(db_path))
tables = db.table_names()

# 1. Get the Sutta Text
sutta_text = ""
if "sutta_knowledge" in tables:
    try:
        s_tbl = db.open_table("sutta_knowledge")
        sutta_df = s_tbl.to_pandas()
        sutta = sutta_df[sutta_df['sutta_id'] == '${sutta_id}'].head(1)
        if not sutta.empty:
            sutta_text = sutta.iloc[0]['text']
    except Exception as e:
        pass

if not sutta_text:
    try:
        import glob
        # Try different possible paths
        search_paths = [
            root / "codex" / "codex4" / "AN ${sutta_id}.json",
            root / "codex" / "codex3" / "AN ${sutta_id}.json"
        ]
        for p in search_paths:
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sutta_text = (data.get("sutta") or "") + " " + (data.get("commentary") or "")
                    break
    except:
        pass

if not sutta_text:
    print(json.dumps({"error": f"Sutta text not found for ${sutta_id}"}))
    exit(0)

# 2. Search
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_vec = model.encode(sutta_text).tolist()

    target_table = None
    for t in ["manga_knowledge", "manga_panels"]:
        if t in tables:
            target_table = t
            break

    if not target_table:
        print(json.dumps({"error": "Manga tables not found in DB"}))
        exit(0)

    tbl = db.open_table(target_table)
    if tbl.count_rows() == 0:
        print(json.dumps({"error": f"Table {target_table} is empty"}))
        exit(0)

    results = tbl.search(query_vec).limit(10).to_pandas()
    if 'vector' in results.columns:
        results = results.drop(columns=['vector'])

    print(results.to_json(orient='records'))
except Exception as e:
    print(json.dumps({"error": str(e)}))
`;

        const result = spawnSync(pythonCommand, ["-c", script], {
          cwd: process.cwd(),
          encoding: "utf8",
          timeout: 60000,
          windowsHide: true,
        });

        if (result.status !== 0) {
           return new Response(JSON.stringify({ error: result.stderr || "Python execution failed" }), { status: 500 });
        }

        try {
            // Check if Python returned a JSON error object
            const parsed = JSON.parse(result.stdout);
            if (parsed.error) {
                console.warn("[LANCE SEARCH ERROR]", parsed.error);
                // Return the error so we can see it in the UI matches
                return new Response(JSON.stringify([{ text: "ERROR: " + parsed.error, id: "error" }]), {
                    headers: { "Content-Type": "application/json" },
                });
            }
            return new Response(result.stdout, {
                headers: { "Content-Type": "application/json; charset=utf-8" },
            });
        } catch(e) {
            return new Response(JSON.stringify([{ text: "ERROR: Invalid JSON from Python: " + result.stdout, id: "error" }]), {
                headers: { "Content-Type": "application/json" },
            });
        }
      },
      PUT: async ({ request }) => {
        const body = await request.json();
        const { sutta_id, panel_id, volume } = body;
        const pythonCommand = process.platform === "win32" ? "python.exe" : "python3";

        const script = `
import lancedb, json, pathlib, warnings
warnings.filterwarnings("ignore")
root = pathlib.Path.cwd()
db_path = root / "data" / "damalance"
db = lancedb.connect(str(db_path))
tbl = db.open_table("manga_knowledge")

# Check if sutta_id column exists, if not, it will be added during update in some versions
# But in LanceDB python, we can use update()
try:
    tbl.update(where=f"id = '{panel_id}' AND volume = '{volume}'", values={"sutta_id": "${sutta_id}"})
    print(json.dumps({"ok": True}))
except Exception as e:
    # If column doesn't exist, we might need to add it or use a different approach
    # For now, let's try a simpler approach if update fails
    try:
        df = tbl.to_pandas()
        if 'sutta_id' not in df.columns:
            df['sutta_id'] = None
        df.loc[(df['id'] == '${panel_id}') & (df['volume'] == '${volume}'), 'sutta_id'] = '${sutta_id}'
        db.create_table("manga_knowledge", data=df, mode="overwrite")
        print(json.dumps({"ok": True}))
    except Exception as e2:
        print(json.dumps({"error": str(e2)}))
`;

        const result = spawnSync(pythonCommand, ["-c", script], {
          cwd: process.cwd(),
          encoding: "utf8",
        });

        return new Response(result.stdout, {
          headers: { "Content-Type": "application/json" },
        });
      }
    },
  },
});
