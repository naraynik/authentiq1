const hre = require("hardhat");
const fs = require("fs");
const path = require("path");
require("dotenv").config();

// Attempt to load backend .env dynamically
const candidatePaths = [
  path.resolve(__dirname, "../backend/.env"),
  path.resolve(__dirname, "../../AUTHENIQ-AI-main/backend/.env"),
  path.resolve(__dirname, "../../backend/.env"),
];
const backendEnvPath = candidatePaths.find(p => fs.existsSync(p)) || candidatePaths[0];

if (fs.existsSync(backendEnvPath)) {
  require("dotenv").config({ path: backendEnvPath, override: true });
}

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const provider = hre.ethers.provider;

  console.log("====================================================");
  console.log("ProductVerification Smart Contract Management");
  console.log("Deploying/Signing Account:", deployer.address);
  const balance = await provider.getBalance(deployer.address);
  console.log("Account Balance:", hre.ethers.formatEther(balance), "ETH");
  console.log("====================================================");

  const existingAddress = process.env.CONTRACT_ADDRESS;
  if (existingAddress && hre.ethers.isAddress(existingAddress)) {
    try {
      const code = await provider.getCode(existingAddress);
      if (code && code !== "0x" && code !== "0x0" && code.length > 2) {
        console.log("REUSING EXISTING CONTRACT STATE");
        console.log("Contract bytecode confirmed on-chain at:", existingAddress);
        console.log("Skipping redeployment to preserve existing registered products.");
        console.log("====================================================");
        return;
      } else {
        console.log("No contract bytecode found at configured address:", existingAddress);
        console.log("Deploying fresh contract instance...");
      }
    } catch (err) {
      console.log("Could not query bytecode at configured address, deploying fresh instance...");
    }
  }

  // Deploy fresh instance of ProductVerification
  console.log("Deploying ProductVerification.sol...");
  const ProductVerification = await hre.ethers.getContractFactory("ProductVerification");
  const contract = await ProductVerification.deploy(deployer.address);

  await contract.waitForDeployment();
  const deployedAddress = await contract.getAddress();

  console.log("SUCCESS: ProductVerification deployed at:", deployedAddress);
  console.log("Deployer account granted DEFAULT_ADMIN_ROLE & MANUFACTURER_ROLE.");
  console.log("====================================================");

  // Update backend/.env CONTRACT_ADDRESS safely without modifying other variables
  if (fs.existsSync(backendEnvPath)) {
    let envContent = fs.readFileSync(backendEnvPath, "utf8");
    if (envContent.includes("CONTRACT_ADDRESS=")) {
      envContent = envContent.replace(/CONTRACT_ADDRESS=".*?"/g, `CONTRACT_ADDRESS="${deployedAddress}"`);
      envContent = envContent.replace(/CONTRACT_ADDRESS='.*?'/g, `CONTRACT_ADDRESS="${deployedAddress}"`);
      envContent = envContent.replace(/CONTRACT_ADDRESS=([^\r\n]+)/g, `CONTRACT_ADDRESS="${deployedAddress}"`);
    } else {
      envContent += `\nCONTRACT_ADDRESS="${deployedAddress}"\n`;
    }
    fs.writeFileSync(backendEnvPath, envContent, "utf8");
    console.log(`Updated CONTRACT_ADDRESS="${deployedAddress}" in ${backendEnvPath}`);
    console.log("NOTE: If FastAPI server is already running, please restart/reload the server to pick up the updated contract address.");
  } else {
    console.log("Set backend .env CONTRACT_ADDRESS to:", deployedAddress);
  }
  console.log("====================================================");
}

main().catch((error) => {
  console.error("Deployment Error:", error);
  process.exitCode = 1;
});
