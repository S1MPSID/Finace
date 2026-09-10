import fs from "fs";
import path from "path";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// The docs are served from backend/public/docs
const docsBaseDir = path.join(__dirname, "../../public/docs");

function superNormalize(str) {
  return str.toLowerCase()
    .replace(/[^a-z0-9]/g, "-") // Replace everything non-alphanumeric with -
    .replace(/-+/g, "-")        // Collapse multiple hyphens
    .replace(/^-|-$/g, "");    // Trim hyphens from ends
}

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

export async function serveDoc(req, res) {
  // Using a regex route `app.get(/^\/docs\/(.*)/, ...)` captures the path in req.params[0]
  const rawPath = req.params[0];
  if (!rawPath) return res.status(400).send("Path required");

  // 1. Try exact match first (handles /AEPS/filename.pdf)
  const directPath = path.join(docsBaseDir, rawPath);
  if (fs.existsSync(directPath) && fs.lstatSync(directPath).isFile()) {
    return res.sendFile(directPath);
  }

  // 2. Fallback to fuzzy recursive search for the filename part
  const filename = path.basename(rawPath);
  const target = superNormalize(filename);

  try {
    const foundPath = findFileRecursive(docsBaseDir, target);
    if (foundPath) {
      return res.sendFile(foundPath);
    }
    res.status(404).json({ ok: false, error: "Document not found", target, attemptedPath: rawPath });
  } catch (error) {
    console.error("Error serving doc:", error);
    res.status(500).json({ ok: false, error: "Server error serving doc" });
  }
}

function findFileRecursive(dir, target) {
  if (!fs.existsSync(dir)) return null;
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      const found = findFileRecursive(fullPath, target);
      if (found) return found;
    } else if (entry.isFile()) {
      const nameWithoutExt = entry.name.replace(/\.[^/.]+$/, "");
      const normalizedEntry = superNormalize(nameWithoutExt);
      
      // Fuzzy matching:
      // 1. Exact normalized match
      // 2. Target contains normalized entry (handles category prefixes like aeps-)
      // 3. Normalized entry contains target
      if (normalizedEntry === target || target.includes(normalizedEntry) || normalizedEntry.includes(target)) {
        return fullPath;
      }
    }
  }
  return null;
}
