import fs from "node:fs";
import os from "node:os";
import path from "node:path";

import { pythonRagDir } from "../config/paths.js";

const venvPython = path.join(pythonRagDir, ".venv", "Scripts", "python.exe");

export function resolvePythonCommand() {
  if (process.env.PYTHON_RAG_EXE) {
    return { exe: process.env.PYTHON_RAG_EXE, extraArgs: [] };
  }

  if (fs.existsSync(venvPython)) {
    return { exe: venvPython, extraArgs: [] };
  }

  const localAppPython = path.join(
    os.homedir(),
    "AppData",
    "Local",
    "Programs",
    "Python",
    "Python312",
    "python.exe"
  );
  if (fs.existsSync(localAppPython)) {
    return { exe: localAppPython, extraArgs: [] };
  }

  const pyLauncher = path.join(process.env.SystemRoot || "C:\\Windows", "py.exe");
  if (fs.existsSync(pyLauncher)) {
    return { exe: pyLauncher, extraArgs: ["-3"] };
  }

  return { exe: "python", extraArgs: [] };
}
