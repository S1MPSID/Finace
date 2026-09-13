import { ethers as ethersLib } from "ethers";
import fs from "node:fs";
import path from "node:path";
import { network } from "hardhat";

async function main() {
  const conn: any = await network.connect();
  if (conn?.ethers?.deployContract) {
    const complianceAudit = await conn.ethers.deployContract("ComplianceAudit");
    await complianceAudit.waitForDeployment();

    const contractAddress = await complianceAudit.getAddress();
    const networkData = await conn.ethers.provider.getNetwork();

    console.log("ComplianceAudit deployed successfully");
    console.log(`Network: ${networkData.name}`);
    console.log(`Address: ${contractAddress}`);
    return;
  }

  // Fallback deploy path: direct ethers + compiled artifact
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
  const factory = new ethersLib.ContractFactory(artifact.abi, artifact.bytecode, wallet);
  const contract = await factory.deploy();
  await contract.waitForDeployment();
  const contractAddress = await contract.getAddress();
  const net = await provider.getNetwork();

  console.log("ComplianceAudit deployed successfully");
  console.log(`Network: ${net.name} (${net.chainId})`);
  console.log(`Address: ${contractAddress}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
