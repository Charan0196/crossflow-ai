import hre from "hardhat";
const { ethers, upgrades } = hre;

/**
 * Simple test to verify deployment infrastructure works
 */
async function main() {
  console.log("🧪 Testing Deployment Infrastructure");
  console.log("===================================");
  
  const [deployer] = await ethers.getSigners();
  console.log(`Deployer: ${deployer.address}`);
  console.log(`Balance: ${ethers.formatEther(await ethers.provider.getBalance(deployer.address))} ETH`);
  console.log("");

  try {
    // Test 1: Deploy MultiSigWallet
    console.log("1️⃣ Testing MultiSigWallet deployment...");
    const MultiSigWallet = await ethers.getContractFactory("MultiSigWallet");
    const multiSig = await MultiSigWallet.deploy(
      [deployer.address], // Single owner for testing
      1 // Single signature required
    );
    await multiSig.waitForDeployment();
    const multiSigAddress = await multiSig.getAddress();
    console.log(`✅ MultiSigWallet deployed: ${multiSigAddress}`);
    
    // Test 2: Deploy SmartEscrowUpgradeable with proxy
    console.log("2️⃣ Testing SmartEscrowUpgradeable deployment...");
    const SmartEscrowUpgradeable = await ethers.getContractFactory("SmartEscrowUpgradeable");
    const escrow = await upgrades.deployProxy(
      SmartEscrowUpgradeable,
      [
        multiSigAddress, // Owner
        [deployer.address], // Governance members
        1 // Governance threshold
      ],
      {
        initializer: "initialize",
        kind: "uups"
      }
    );
    await escrow.waitForDeployment();
    const escrowAddress = await escrow.getAddress();
    console.log(`✅ SmartEscrowUpgradeable deployed: ${escrowAddress}`);
    
    // Test 3: Verify basic functionality
    console.log("3️⃣ Testing basic functionality...");
    const version = await escrow.getVersion();
    const owner = await escrow.owner();
    const timeoutPeriod = await escrow.timeoutPeriod();
    
    console.log(`   Version: ${version}`);
    console.log(`   Owner: ${owner}`);
    console.log(`   Timeout Period: ${timeoutPeriod} seconds`);
    
    // Test 4: Test upgrade preparation
    console.log("4️⃣ Testing upgrade preparation...");
    await upgrades.validateUpgrade(escrowAddress, SmartEscrowUpgradeable);
    console.log("✅ Upgrade validation passed");
    
    console.log("");
    console.log("🎉 All tests passed! Deployment infrastructure is working correctly.");
    
    return {
      multiSigWallet: multiSigAddress,
      smartEscrow: escrowAddress,
      version: Number(version),
      owner,
      timeoutPeriod: Number(timeoutPeriod)
    };
    
  } catch (error) {
    console.error("❌ Test failed:", error.message);
    throw error;
  }
}

main()
  .then((result) => {
    console.log("\n📊 Test Results:");
    console.log(JSON.stringify(result, null, 2));
    process.exit(0);
  })
  .catch((error) => {
    console.error("❌ Test failed:", error);
    process.exit(1);
  });