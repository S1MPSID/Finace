import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export const repoRoot = path.resolve(__dirname, "..", "..", "..");
export const backendRoot = path.resolve(__dirname, "..", "..");
export const pythonRagDir = path.join(repoRoot, "python-rag");
export const blockchainDir = path.join(repoRoot, "Blockchain");
