import { createFileRoute } from "@tanstack/react-router";
import { spawnSync } from "node:child_process";

export const Route = createFileRoute("/pipeline-events-api")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const url = new URL(request.url);
        const limit = url.searchParams.get("limit") || "100";
        const pythonCommand = process.platform === "win32" ? "python.exe" : "python3";

        const result = spawnSync(
          pythonCommand,
          [
            "-m",
            "uv",
            "run",
            "python",
            "-m",
            "scripts.pipeline.streaming.status",
            "events",
            "--limit",
            limit,
            "--json",
          ],
          {
            cwd: process.cwd(),
            encoding: "utf8",
            timeout: 10000,
            windowsHide: true,
          },
        );

        if (result.status !== 0) {
          console.error("Pipeline events error:", result.stderr);
          return new Response(JSON.stringify([]), {
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
