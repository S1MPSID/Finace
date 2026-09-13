import {
  ensureEnum,
  ensureObject,
  ensureOptionalString,
  ensureString,
} from "../utils/validation.js";

const riskLevels = ["LOW", "MEDIUM", "HIGH"];

export function validateStoreProofRequest(req) {
  ensureObject(req.body, "body");

  return {
    reportId: ensureString(req.body.reportId, "reportId", { minLength: 3, maxLength: 120 }),
    ipfsCid: ensureString(req.body.ipfsCid, "ipfsCid", { minLength: 10, maxLength: 255 }),
    documentHash: ensureString(req.body.documentHash, "documentHash", {
      minLength: 10,
      maxLength: 132,
    }),
    orgName: ensureString(req.body.orgName, "orgName", { minLength: 2, maxLength: 120 }),
    riskLevel: ensureEnum(req.body.riskLevel, "riskLevel", riskLevels, { required: true }),
    contractAddress:
      ensureOptionalString(req.body.contractAddress, "contractAddress", {
        minLength: 10,
        maxLength: 120,
      }) ?? null,
  };
}
