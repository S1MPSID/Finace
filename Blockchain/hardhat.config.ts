import "dotenv/config";
import "@nomicfoundation/hardhat-toolbox-mocha-ethers";
import type { HardhatUserConfig } from "hardhat/config";

const config: HardhatUserConfig = {
  solidity: "0.8.28",
  networks: {
    localhost: {
      type: "http",
      chainType: "l1",
      url: "http://127.0.0.1:8545",
    },
    ganache: {
      type: "http",
      chainType: "l1",
      url: "http://127.0.0.1:8545",
    },
    baseSepolia: {
      type: "http",
      chainType: "l1",
      url: "https://base-sepolia.infura.io/v3/e89118953dec43dba953b54a30da35a3",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY.trim()] : [],
    },
  },
};

export default config;
