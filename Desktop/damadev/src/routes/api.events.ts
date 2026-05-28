import { createFileRoute } from "@tanstack/react-router";
import { spawnSync } from "node:child_process";
import path from "node:path";

export const Route = createFileRoute("/api/events")({
  server: {
    handlers: {
      GET: async () => {
        const pythonCommand = process.platform === "win32" ? "python.exe" : "python3";
        const script = `
import sqlite3, json, pathlib
root = pathlib.Path.cwd()
db_path = root / "data" / "work" / "streaming" / "pipeline.sqlite3"
if not db_path.exists():
    print(json.dumps([]))
    exit(0)
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
try:
    # Try the legacy 'events' table first for direct display
    rows = conn.execute("SELECT * FROM events ORDER BY timestamp DESC LIMIT 200").fetchall()
    print(json.dumps([dict(r) for r in rows]))
except sqlite3.OperationalError:
    # Fallback to 'pipeline_events' if 'events' doesn't exist
    try:
        rows = conn.execute("""
            SELECT event_id as id, occurred_at as timestamp, correlation_id as vid,
                   event_type as stage, 'INFO' as status, payload_json as message
            FROM pipeline_events
            ORDER BY occurred_at DESC LIMIT 200
        """).fetchall()
        print(json.dumps([dict(r) for r in rows]))
    except:
        print(json.dumps([]))
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
    },
  },
});
