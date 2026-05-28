import { createFileRoute } from "@tanstack/react-router";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { uuid } from "uuidv4"; // Assuming uuidv4 is available, or use a simple timestamp-based ID

export const Route = createFileRoute("/work-api/replay")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const body = await request.json();
        const suttaId = String(body?.sutta_id || "").trim();
        const stages = Array.isArray(body?.stages) ? body.stages : ["translate"]; // Default to translate if not specified

        if (!suttaId) {
          return new Response(JSON.stringify({ ok: false, error: "Missing sutta_id" }), {
            status: 400,
            headers: { "Content-Type": "application/json" },
          });
        }

        const pythonCommand = process.platform === "win32" ? "python.exe" : "python3";

        // Instead of spawning the runner directly, we insert a "Tick" into the jobs table.
        // This ensures the Replay follows the Tickerplant rules and waits for the GPU lock.
        const firstStage = stages[0];
        const script = `
import sqlite3, uuid, datetime
db_path = "C:/Users/ADMIN/Desktop/damadev/data/work/streaming/pipeline.sqlite3"
conn = sqlite3.connect(db_path)
job_id = f"replay_{uuid.uuid4().hex[:8]}"
now = datetime.datetime.utcnow().isoformat() + "Z"
conn.execute("""
    INSERT INTO jobs (job_id, event_id, worker_type, sutta_id, status, created_at)
    VALUES (?, ?, ?, ?, 'PENDING', ?)
""", (job_id, f"replay_{suttaId}", "${firstStage}", "${suttaId}", now))
conn.commit()
conn.close()
print(job_id)
`;

        const result = spawnSync(pythonCommand, ["-c", script]);

        if (result.status !== 0) {
          return new Response(JSON.stringify({ ok: false, error: "Failed to queue replay" }), { status: 500 });
        }

        console.log(`[REPLAY QUEUED] Sutta: ${suttaId} Stage: ${firstStage}`);

        return new Response(
          JSON.stringify({ ok: true, message: `Replay for ${suttaId} queued at stage ${firstStage}` }),
          {
            headers: { "Content-Type": "application/json" },
          },
        );
      },
    },
  },
});
