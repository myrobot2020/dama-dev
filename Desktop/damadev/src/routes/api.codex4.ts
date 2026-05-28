import { createFileRoute } from "@tanstack/react-router";
import path from "node:path";
import fs from "node:fs";

export const Route = createFileRoute("/api/codex4")({
  server: {
    handlers: {
      GET: async ({ request }) => {
        const url = new URL(request.url);
        const filename = url.searchParams.get("file");
        const codex4Dir = path.join(process.cwd(), "codex", "codex4");

        if (filename) {
          const dirs = [
            path.join(process.cwd(), "codex", "codex4"),
            path.join(process.cwd(), "codex", "codex3")
          ];

          let filePath = "";
          for (const dir of dirs) {
            const candidate = path.join(dir, path.basename(filename));
            if (fs.existsSync(candidate)) {
              filePath = candidate;
              break;
            }
          }

          if (filePath) {
            const content = fs.readFileSync(filePath, 'utf-8');
            return new Response(content, {
              headers: { "Content-Type": "application/json; charset=utf-8" },
            });
          }
          return new Response("Not found", { status: 404 });
        }

        // List files
        try {
          const dirs = [
            path.join(process.cwd(), "codex", "codex4"),
            path.join(process.cwd(), "codex", "codex3")
          ];

          let allFiles: any[] = [];
          for (const dir of dirs) {
            if (!fs.existsSync(dir)) continue;
            const files = fs.readdirSync(dir)
              .filter(f => f.startsWith("AN ") && f.endsWith(".json"))
              .map(f => {
                const filePath = path.join(dir, f);
                const stats = fs.statSync(filePath);
                try {
                  const content = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
                  return {
                    name: f,
                    id: content.sutta_id,
                    title: content.sutta_name_en,
                    valid: content.valid,
                    tagged: content.tagged,
                    size: stats.size,
                    mtime: stats.mtime.getTime(),
                    dir: path.basename(dir)
                  };
                } catch {
                  return null;
                }
              }).filter(Boolean);
            allFiles = [...allFiles, ...files];
          }

          return new Response(JSON.stringify(allFiles), {
            headers: { "Content-Type": "application/json; charset=utf-8" },
          });
        } catch (e) {
          console.error("Failed to list codex4 files", e);
          return new Response(JSON.stringify({ error: String(e) }), {
            status: 500,
            headers: { "Content-Type": "application/json" },
          });
        }
      },
      POST: async ({ request }) => {
        try {
          const body = await request.json();
          const { sutta_id, updates } = body;
          const dirs = [
            path.join(process.cwd(), "codex", "codex4"),
            path.join(process.cwd(), "codex", "codex3")
          ];
          const filename = `AN ${sutta_id}.json`;

          let filePath = "";
          for (const dir of dirs) {
            const candidate = path.join(dir, filename);
            if (fs.existsSync(candidate)) {
              filePath = candidate;
              break;
            }
          }

          if (!filePath) {
            return new Response("File not found", { status: 404 });
          }

          const currentContent = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
          const newContent = { ...currentContent, ...updates };
          fs.writeFileSync(filePath, JSON.stringify(newContent, null, 2), 'utf-8');

          return new Response(JSON.stringify({ ok: true }), {
            headers: { "Content-Type": "application/json" },
          });
        } catch (e) {
          return new Response(JSON.stringify({ error: String(e) }), { status: 500 });
        }
      }
    },
  },
});
