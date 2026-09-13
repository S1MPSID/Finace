import { getBlockchainDeployment, storeComplianceProof } from "../services/blockchainService.js";

export async function getDeployment(_req, res) {
  const deployment = getBlockchainDeployment();
  res.json({
    ok: true,
    deployment,
  });
}

export async function createProof(req, res) {
  const result = await storeComplianceProof(req.validated);
  res.status(201).json(result);
}
