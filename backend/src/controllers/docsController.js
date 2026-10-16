import fs from "fs";
import path from "path";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// The docs are served from backend/public/docs
const docsBaseDir = path.join(__dirname, "../../public/docs");

export async function getDocsTree(req, res) {
  try {
    const tree = [];

    if (!fs.existsSync(docsBaseDir)) {
      return res.json({ ok: true, data: [] });
    }

    const categories = fs.readdirSync(docsBaseDir, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);

    for (const category of categories) {
      const categoryPath = path.join(docsBaseDir, category);
      const files = fs.readdirSync(categoryPath, { withFileTypes: true })
        .filter(dirent => dirent.isFile() && dirent.name.endsWith('.pdf'))
        .map(dirent => ({
          name: dirent.name,
          path: `${category}/${dirent.name}`
        }));

      if (files.length > 0) {
        tree.push({
          category,
          files
        });
      }
    }

    res.json({ ok: true, data: tree });
  } catch (error) {
    console.error("Error reading docs tree:", error);
    res.status(500).json({ ok: false, error: "Failed to read documents tree" });
  }
}
