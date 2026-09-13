import "dotenv/config";
import fs from "node:fs";
import path from "node:path";
import { ethers as ethersLib } from "ethers";
import { network } from "hardhat";

function parseArgs() {
  const argv = process.argv.slice(2);
  const get = (flag: string) => {
    const idx = argv.indexOf(flag);
    return idx >= 0 ? argv[idx + 1] : "";
  };
  const reportId = get("--report-id") || process.env.REPORT_ID || "";
  const ipfsCid = get("--ipfs-cid") || process.env.IPFS_CID || "";
  const documentHash = get("--document-hash") || process.env.DOCUMENT_HASH || "";
  const orgName = get("--org-name") || process.env.ORG_NAME || "";
  const riskLevel = get("--risk-level") || process.env.RISK_LEVEL || "";
  const contractAddress = get("--contract") || process.env.CONTRACT_ADDRESS || "";

  if (!reportId || !ipfsCid || !documentHash || !orgName || !riskLevel || !contractAddress) {
    throw new Error(
      "Missing args. Required: --report-id --ipfs-cid --document-hash --org-name --risk-level --contract (or env vars REPORT_ID, IPFS_CID, DOCUMENT_HASH, ORG_NAME, RISK_LEVEL, CONTRACT_ADDRESS)"
    );
  }
  return { reportId, ipfsCid, documentHash, orgName, riskLevel, contractAddress };
}

async function main() {
  const args = parseArgs();
  const conn: any = await network.connect();

  if (conn?.ethers?.getContractAt) {
    const contract = await conn.ethers.getContractAt("ComplianceAudit", args.contractAddress);
    const tx = await contract.storeReport(
      args.reportId,
      args.ipfsCid,
      args.documentHash,
      conn.ethers.encodeBytes32String(args.orgName.slice(0, 31)),
      args.riskLevel
    );
    const receipt = await tx.wait();
    console.log("storeReport tx mined");
    console.log(`txHash: ${tx.hash}`);
    console.log(`blockNumber: ${receipt?.blockNumber ?? "unknown"}`);
    return;
  }

  const rpcUrl = process.env.BASE_SEPOLIA_RPC_URL || "https://base-sepolia.infura.io/v3/e89118953dec43dba953b54a30da35a3";
  const privateKey = process.env.PRIVATE_KEY || "";
  if (!privateKey) {
    throw new Error("PRIVATE_KEY missing in environment");
  }
  const artifactPath = path.resolve("artifacts/contracts/Compliance.sol/ComplianceAudit.json");
  if (!fs.existsSync(artifactPath)) {
    throw new Error(`Artifact not found: ${artifactPath}. Run npm run build first.`);
  }
  const artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8"));
  const provider = new ethersLib.JsonRpcProvider(rpcUrl);
  const wallet = new ethersLib.Wallet(privateKey.trim(), provider);
  const contract = new ethersLib.Contract(args.contractAddress, artifact.abi, wallet);
  const tx = await contract.storeReport(
    args.reportId,
    args.ipfsCid,
    args.documentHash,
    ethersLib.encodeBytes32String(args.orgName.slice(0, 31)),
    args.riskLevel
  );
  const receipt = await tx.wait();

  console.log("storeReport tx mined");
  console.log(`txHash: ${tx.hash}`);
  console.log(`blockNumber: ${receipt?.blockNumber ?? "unknown"}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
