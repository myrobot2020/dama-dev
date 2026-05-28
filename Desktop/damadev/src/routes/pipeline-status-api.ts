import { createFileRoute } from "@tanstack/react-router";
import { spawnSync } from "node:child_process";

export const Route = createFileRoute("/pipeline-status-api")({
  server: {
    handlers: {
      GET: async () => {
        const pythonCommand = process.platform === "win32" ? "python.exe" : "python3";
        const result = spawnSync(
          pythonCommand,
          ["-m", "uv", "run", "python", "-m", "scripts.pipeline.streaming.status", "snapshot"],
          {
            cwd: process.cwd(),
            encoding: "utf8",
            timeout: 10000,
            windowsHide: true,
          },
        );

        if (result.status !== 0) {
          console.error("Pipeline status error:", result.stderr);
          return new Response(
            JSON.stringify({ error: result.stderr || "snapshot failed" }),
            {
              status: 500,
              headers: { "Content-Type": "application/json" },
            },
          );
        }

        return new Response(result.stdout, {
          headers: { "Content-Type": "application/json; charset=utf-8" },
        });
      },
    },
  },
});
