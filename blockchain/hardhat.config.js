require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

const SEPOLIA_RPC_URL = process.env.SEPOLIA_RPC_URL || "";
const SEPOLIA_PRIVATE_KEY = process.env.SEPOLIA_PRIVATE_KEY || "";
const ETHERSCAN_API_KEY = process.env.ETHERSCAN_API_KEY || "";
const GANACHE_PRIVATE_KEY = process.env.GANACHE_PRIVATE_KEY || "";

const accounts = [];
if (SEPOLIA_PRIVATE_KEY) {
  accounts.push(SEPOLIA_PRIVATE_KEY);
}

const ganacheAccounts = [];
if (GANACHE_PRIVATE_KEY) {
  ganacheAccounts.push(GANACHE_PRIVATE_KEY);
}

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: {
      viaIR: true,
      optimizer: {
        enabled: true,
        runs: 200,
      },
    },
  },
  networks: {
    hardhat: {
      chainId: 1337,
    },
    ganache: {
      url: process.env.GANACHE_RPC_URL || process.env.RPC_URL || "http://127.0.0.1:8545",
      chainId: parseInt(process.env.CHAIN_ID || "1337"),
      accounts: ganacheAccounts.length > 0 ? ganacheAccounts : undefined,
    },
    sepolia: {
      url: SEPOLIA_RPC_URL,
      accounts: accounts,
      chainId: 11155111,
    },
  },
  etherscan: {
    apiKey: {
      sepolia: ETHERSCAN_API_KEY,
    },
  },
};
