export const CONTRACT_ADDRESS = "0xF1FB4e26CdeF0927dD8AC9e6633fFdFe42EFc150";

export const COMPLIANCE_ABI = [
  {
    "inputs": [
      { "internalType": "string", "name": "_reportId", "type": "string" }
    ],
    "name": "getReport",
    "outputs": [
      { "internalType": "string", "name": "reportId", "type": "string" },
      { "internalType": "string", "name": "ipfsCid", "type": "string" },
      { "internalType": "bytes32", "name": "documentHash", "type": "bytes32" },
      { "internalType": "bytes32", "name": "orgName", "type": "bytes32" },
      { "internalType": "string", "name": "riskLevel", "type": "string" },
      { "internalType": "uint256", "name": "timestamp", "type": "uint256" },
      { "internalType": "bool", "name": "verified", "type": "bool" },
      { "internalType": "address", "name": "verifiedBy", "type": "address" },
      { "internalType": "string", "name": "remarks", "type": "string" }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "string", "name": "_reportId", "type": "string" },
      { "internalType": "string", "name": "_ipfsCid", "type": "string" },
      { "internalType": "bytes32", "name": "_documentHash", "type": "bytes32" },
      { "internalType": "bytes32", "name": "_orgName", "type": "bytes32" },
      { "internalType": "string", "name": "_riskLevel", "type": "string" }
    ],
    "name": "storeReport",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
];
