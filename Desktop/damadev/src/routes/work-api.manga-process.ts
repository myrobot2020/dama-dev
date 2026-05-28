import { createFileRoute } from "@tanstack/react-router";
import { spawn } from "node:child_process";
import path from "node:path";

export const Route = createFileRoute("/work-api/manga-process")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const body = await request.json();
        const { volume, limit, prompt, force } = body;

        // Path to the dama-manga scripts
        const mangaScriptsDir = "C:/Users/ADMIN/Desktop/damamanga";
        const pythonCommand = process.platform === "win32" ? "python.exe" : "python3";

        const args = [
            "scripts/manga/panel_processor.py",
            "--volume", volume || "buddha_v01",
        ];

        if (limit) args.push("--limit", limit.toString());
        if (prompt) args.push("--prompt", prompt);
        if (force) args.push("--force");

        console.log("Spawning manga processor with args:", args);

        const child = spawn(pythonCommand, args, {
          cwd: mangaScriptsDir,
          detached: true,
          stdio: "ignore",
          windowsHide: true,
        });

        child.unref();

        return new Response(
          JSON.stringify({
            ok: true,
            message: `Manga processing started for ${volume || "buddha_v01"}`,
            pid: child.pid
          }),
          { headers: { "Content-Type": "application/json" } }
        );
      },
    },
  },
});
