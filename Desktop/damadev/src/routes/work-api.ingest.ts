import { createFileRoute } from "@tanstack/react-router";
import { spawnSync } from "node:child_process";

export const Route = createFileRoute("/work-api/ingest")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const url = new URL(request.url);
        const urlParam = url.searchParams.get("url");

        if (!urlParam) {
          return new Response(JSON.stringify({ error: "Missing url parameter" }), {
            status: 400,
            headers: { "Content-Type": "application/json" },
          });
        }

        const pythonCommand = process.platform === "win32" ? "python.exe" : "python3";

        // Push the URL into the 'ingest' queue.
        // This allows the SUB_IO worker to handle it sequentially and safely.
        const script = `
import sqlite3, uuid, datetime
db_path = "C:/Users/ADMIN/Desktop/damadev/data/work/streaming/pipeline.sqlite3"
conn = sqlite3.connect(db_path)
job_id = f"ingest_{uuid.uuid4().hex[:8]}"
now = datetime.datetime.utcnow().isoformat() + "Z"
# We store the URL in the sutta_id field temporarily for the ingest stage
conn.execute("""
    INSERT INTO jobs (job_id, event_id, worker_type, sutta_id, status, created_at)
    VALUES (?, ?, 'ingest', ?, 'PENDING', ?)
""", (job_id, f"url_{hash('${urlParam}')}", "${urlParam}", now))
conn.commit()
conn.close()
`;

        spawnSync(pythonCommand, ["-c", script]);

        console.log(`[INGEST QUEUED] URL: ${urlParam}`);

        return new Response(
          JSON.stringify({ ok: true, message: "URL added to ingest queue" }),
          {
            headers: { "Content-Type": "application/json" },
          },
        );
      },
    },
  },
});
