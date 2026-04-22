import hre from "hardhat";
const { ethers } = hre;

async function main() {
  console.log("🚀 CrossFlow AI Phase 1 - Smart Contract Deployment");
  console.log("==================================================");
  
  const [deployer] = await ethers.getSigners();
  const network = hre.network.name;
  const chainId = hre.network.config.chainId;
  
  console.log(`Network: ${network} (Chain ID: ${chainId})`);
  console.log(`Deployer: ${deployer.address}`);
  console.log(`Balance: ${ethers.formatEther(await ethers.provider.getBalance(deployer.address))} ETH`);
  console.log("");

  // Deploy TestContract for now (will be replaced with actual contracts)
  console.log("📄 Deploying TestContract...");
  const TestContract = await ethers.getContractFactory("TestContract");
  const testContract = await TestContract.deploy("CrossFlow AI Phase 1 Infrastructure Ready!");
  
  await testContract.waitForDeployment();
  const testContractAddress = await testContract.getAddress();
  
  console.log(`✅ TestContract deployed to: ${testContractAddress}`);
  console.log("");
  
  // Verify deployment
  console.log("🔍 Verifying deployment...");
  const message = await testContract.getMessage();
  console.log(`Message: ${message}`);
  
  console.log("");
  console.log("🎉 Deployment completed successfully!");
  console.log("==================================================");
  
  return {
    testContract: testContractAddress,
  };
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("❌ Deployment failed:");
    console.error(error);
    process.exit(1);
  });