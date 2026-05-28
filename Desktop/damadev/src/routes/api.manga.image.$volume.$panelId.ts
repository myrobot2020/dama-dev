import { createFileRoute } from "@tanstack/react-router";
import fs from "node:fs";
import path from "node:path";

export const Route = createFileRoute("/api/manga/image/$volume/$panelId")({
  server: {
    handlers: {
      GET: async ({ params }) => {
        const { volume, panelId } = params as { volume: string; panelId: string };

        const mangaBasePath = "C:/Users/ADMIN/Desktop/damamanga/data/manga/mobile";
        let filePath = path.join(mangaBasePath, volume, `${panelId}.webp`);

        if (!fs.existsSync(filePath)) {
          // Extract the unique part of the panel ID (e.g., p0333_panel03)
          const panelMatch = panelId.match(/p\d+_panel\d+/);
          const suffix = panelMatch ? panelMatch[0] : panelId;

          // Search all volume directories for a file containing this suffix
          const volumes = fs.readdirSync(mangaBasePath).filter(f => fs.statSync(path.join(mangaBasePath, f)).isDirectory());
          for (const v of volumes) {
            const dirPath = path.join(mangaBasePath, v);
            const files = fs.readdirSync(dirPath);
            const match = files.find(f => f.includes(suffix) && f.endsWith(".webp"));
            if (match) {
              filePath = path.join(dirPath, match);
              break;
            }
          }
        }

        if (fs.existsSync(filePath)) {
          const imageBuffer = fs.readFileSync(filePath);
          return new Response(imageBuffer, {
            headers: {
              "Content-Type": "image/webp",
              "Cache-Control": "public, max-age=31536000, immutable",
            },
          });
        }

        return new Response("Image not found", { status: 404 });
      },
    },
  },
});
