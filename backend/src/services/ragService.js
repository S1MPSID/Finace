import { spawn } from "node:child_process";

import { env } from "../config/env.js";
import { pythonRagDir } from "../config/paths.js";
import { HttpError } from "../utils/httpError.js";
import { resolvePythonCommand } from "../utils/python.js";
import { postJson } from "./httpClient.js";

export async function runGeneralQuery(input) {
  if (env.ragProviderMode === "http") {
    return runHttpQuery(input);
  }
  return runCliQuery(input);
}

async function runHttpQuery({ prompt, topK = 5, regulator = null, category = null }) {
  const maxChars = env.ragPromptMaxChars;
  const trimmedPrompt =
    prompt.length > maxChars ? prompt.slice(prompt.length - maxChars) : prompt;

  return postJson(
    `${env.fastApiBaseUrl}/query`,
    {
      prompt: trimmedPrompt,
      top_k: topK,
      regulator,
      category,
    },
    { timeoutMs: env.fastApiTimeoutMs }
  );
}

async function runCliQuery({ prompt, topK = 5, regulator = null, category = null }) {
  return new Promise((resolve, reject) => {
    const py = resolvePythonCommand();
    const args = [
      ...py.extraArgs,
      "-m",
      "api.general_query",
      "--prompt",
      prompt,
      "--top-k",
      String(topK),
    ];

    if (regulator) args.push("--regulator", regulator);
    if (category) args.push("--category", category);

    const child = spawn(py.exe, args, {
      cwd: pythonRagDir,
      env: {
        ...process.env,
        PYTHONWARNINGS: "ignore",
      },
      windowsHide: true,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });

    child.on("error", (error) => {
      if (error.code === "ENOENT") {
        reject(
          new HttpError(
            500,
            "python_not_found",
            "Python executable not found. Set PYTHON_RAG_EXE or create python-rag/.venv."
          )
        );
        return;
      }
      reject(error);
    });

    child.on("close", (code) => {
      if (code !== 0) {
        reject(new HttpError(502, "rag_process_failed", stderr || `Python exited with code ${code}`));
        return;
      }

      try {
        // Find the first '{' and last '}' to extract only the JSON part
        const start = stdout.indexOf("{");
        const end = stdout.lastIndexOf("}");
        if (start === -1 || end === -1) {
          throw new Error("No JSON object found in output");
        }
        const jsonStr = stdout.substring(start, end + 1);
        resolve(JSON.parse(jsonStr));
      } catch (error) {
        reject(
          new HttpError(
            502,
            "rag_invalid_response",
            `Invalid JSON from python service: ${error.message}`,
            {
              stdout,
              stderr,
            }
          )
        );
      }
    });
  });
}

export async function runRegulationSearch({ query, topK = 10, regulator = null }) {
  return postJson(
    `${env.fastApiBaseUrl}/search`,
    {
      query,
      top_k: topK,
      regulator,
    },
    { timeoutMs: env.fastApiTimeoutMs }
  );
}
