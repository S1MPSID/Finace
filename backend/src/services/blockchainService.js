import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

import { env } from "../config/env.js";
import { blockchainDir, repoRoot } from "../config/paths.js";
import { HttpError } from "../utils/httpError.js";

const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";

export function getBlockchainDeployment() {
  const deploymentPath = path.join(repoRoot, env.blockchainDeploymentFile);
  if (!fs.existsSync(deploymentPath)) {
    throw new HttpError(
      503,
      "blockchain_not_configured",
      `Deployment file not found at ${env.blockchainDeploymentFile}`
    );
  }

  const content = fs.readFileSync(deploymentPath, "utf8");
  return JSON.parse(content);
}

export async function storeComplianceProof(payload) {
  if (!env.blockchainWriteEnabled) {
    throw new HttpError(503, "blockchain_write_disabled", "Blockchain writes are disabled");
  }

  const deployment = getBlockchainDeployment();
  const contractAddress = payload.contractAddress || deployment.address;

  return new Promise((resolve, reject) => {
    const child = spawn(npmCommand, ["run", env.blockchainStoreScript], {
      cwd: blockchainDir,
      env: {
        ...process.env,
        REPORT_ID: payload.reportId,
        IPFS_CID: payload.ipfsCid,
        DOCUMENT_HASH: payload.documentHash,
        ORG_NAME: payload.orgName,
        RISK_LEVEL: payload.riskLevel,
        CONTRACT_ADDRESS: contractAddress,
      },
      windowsHide: true,
      shell: process.platform === "win32",
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
      reject(new HttpError(502, "blockchain_process_failed", error.message));
    });

    child.on("close", (code) => {
      if (code !== 0) {
        reject(
          new HttpError(
            502,
            "blockchain_store_failed",
            stderr || `Blockchain writer exited with code ${code}`,
            { stdout, stderr }
          )
        );
        return;
      }

      resolve({
        ok: true,
        network: env.blockchainNetwork,
        contractAddress,
        transactionHash: readLabeledValue(stdout, "txHash"),
        blockNumber: readLabeledValue(stdout, "blockNumber"),
        rawOutput: stdout.trim(),
      });
    });
  });
}

function readLabeledValue(output, label) {
  const match = output.match(new RegExp(`${label}:\\s*(.+)`, "i"));
  return match ? match[1].trim() : null;
}
