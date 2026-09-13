import { env } from "../config/env.js";
import { getBlockchainDeployment } from "../services/blockchainService.js";

export async function getHealth(_req, res) {
  let blockchain = { ok: false, configured: false };

  try {
    const deployment = getBlockchainDeployment();
    blockchain = {
      ok: true,
      configured: true,
      network: deployment.network,
      contractAddress: deployment.address,
    };
  } catch {
    blockchain = { ok: false, configured: false };
  }

  res.json({
    ok: true,
    service: env.serviceName,
    environment: env.nodeEnv,
    ragProviderMode: env.ragProviderMode,
    fastApiBaseUrl: env.fastApiBaseUrl,
    blockchain,
  });
}
