import hre from "hardhat";
const { ethers, upgrades } = hre;

/**
 * CrossFlow AI Phase 1 - Smart Escrow Upgrade Script
 * Handles upgrades to SmartEscrowUpgradeable using UUPS proxy pattern
 */

// Deployed contract addresses (update these after deployment)
const DEPLOYED_ADDRESSES = {
  ethereum: {
    escrowProxy: "", // Add after deployment
    multiSig: "",    // Add after deployment
  },
  arbitrum: {
    escrowProxy: "", // Add after deployment
    multiSig: "",    // Add after deployment
  },
  sepolia: {
    escrowProxy: "0x...", // Add after deployment
    multiSig: "0x...",    // Add after deployment
  },
  arbitrumSepolia: {
    escrowProxy: "0x...", // Add after deployment
    multiSig: "0x...",    // Add after deployment
  },
};

async function validateUpgrade(proxyAddress, newImplementationFactory) {
  console.log("🔍 Validating upgrade compatibility...");
  
  try {
    // Validate that the upgrade is safe
    await upgrades.validateUpgrade(proxyAddress, newImplementationFactory);
    console.log("✅ Upgrade validation passed");
    return true;
  } catch (error) {
    console.error("❌ Upgrade validation failed:", error.message);
    return false;
  }
}

async function prepareUpgrade(proxyAddress, newImplementationFactory) {
  console.log("📦 Preparing upgrade implementation...");
  
  try {
    // Prepare the upgrade (deploys new implementation)
    const newImplementationAddress = await upgrades.prepareUpgrade(
      proxyAddress,
      newImplementationFactory
    );
    
    console.log(`✅ New implementation prepared: ${newImplementationAddress}`);
    return newImplementationAddress;
  } catch (error) {
    console.error("❌ Failed to prepare upgrade:", error.message);
    throw error;
  }
}

async function executeUpgrade(proxyAddress, newImplementationFactory) {
  console.log("🚀 Executing upgrade...");
  
  try {
    // Execute the upgrade
    const upgradedContract = await upgrades.upgradeProxy(
      proxyAddress,
      newImplementationFactory
    );
    
    await upgradedContract.waitForDeployment();
    
    console.log("✅ Upgrade executed successfully");
    
    // Verify the upgrade
    const newVersion = await upgradedContract.getVersion();
    console.log(`   New version: ${newVersion}`);
    
    return upgradedContract;
  } catch (error) {
    console.error("❌ Failed to execute upgrade:", error.message);
    throw error;
  }
}

async function createUpgradeProposal(multiSigAddress, proxyAddress, newImplementationAddress) {
  console.log("📋 Creating multi-sig upgrade proposal...");
  
  try {
    // Get the multi-sig wallet contract
    const MultiSigWallet = await ethers.getContractFactory("MultiSigWallet");
    const multiSig = MultiSigWallet.attach(multiSigAddress);
    
    // Get the proxy admin interface
    const SmartEscrowUpgradeable = await ethers.getContractFactory("SmartEscrowUpgradeable");
    const escrowContract = SmartEscrowUpgradeable.attach(proxyAddress);
    
    // Encode the upgrade function call
    const upgradeCalldata = escrowContract.interface.encodeFunctionData(
      "upgradeToAndCall",
      [newImplementationAddress, "0x"] // No additional initialization data
    );
    
    // Submit transaction to multi-sig
    const tx = await multiSig.submitTransaction(
      proxyAddress,
      0, // No ETH value
      upgradeCalldata
    );
    
    const receipt = await tx.wait();
    
    // Extract transaction ID from events
    const submissionEvent = receipt.logs.find(
      log => log.fragment && log.fragment.name === "Submission"
    );
    
    const transactionId = submissionEvent ? submissionEvent.args[0] : null;
    
    console.log(`✅ Upgrade proposal created`);
    console.log(`   Transaction ID: ${transactionId}`);
    console.log(`   Multi-sig address: ${multiSigAddress}`);
    console.log(`   Target: ${proxyAddress}`);
    console.log(`   New implementation: ${newImplementationAddress}`);
    
    return transactionId;
  } catch (error) {
    console.error("❌ Failed to create upgrade proposal:", error.message);
    throw error;
  }
}

async function checkUpgradeStatus(multiSigAddress, transactionId) {
  console.log("📊 Checking upgrade proposal status...");
  
  try {
    const MultiSigWallet = await ethers.getContractFactory("MultiSigWallet");
    const multiSig = MultiSigWallet.attach(multiSigAddress);
    
    // Get transaction details
    const transaction = await multiSig.transactions(transactionId);
    const confirmationCount = await multiSig.getConfirmationCount(transactionId);
    const required = await multiSig.required();
    const isConfirmed = await multiSig.isConfirmed(transactionId);
    
    console.log(`   Transaction ID: ${transactionId}`);
    console.log(`   Confirmations: ${confirmationCount}/${required}`);
    console.log(`   Status: ${transaction.executed ? "Executed" : isConfirmed ? "Ready to Execute" : "Pending"}`);
    
    if (isConfirmed && !transaction.executed) {
      console.log("🎯 Proposal is ready for execution!");
    }
    
    return {
      transactionId,
      confirmationCount: Number(confirmationCount),
      required: Number(required),
      isConfirmed,
      executed: transaction.executed
    };
  } catch (error) {
    console.error("❌ Failed to check upgrade status:", error.message);
    throw error;
  }
}

async function main() {
  console.log("🔄 CrossFlow AI Phase 1 - Smart Escrow Upgrade");
  console.log("===============================================");
  
  const [deployer] = await ethers.getSigners();
  const network = hre.network.name;
  
  console.log(`Network: ${network}`);
  console.log(`Deployer: ${deployer.address}`);
  console.log("");

  // Get deployed addresses for current network
  const addresses = DEPLOYED_ADDRESSES[network];
  if (!addresses || !addresses.escrowProxy) {
    throw new Error(`No deployed addresses found for network: ${network}`);
  }
  
  console.log(`📋 Current Deployment:`);
  console.log(`   Escrow Proxy: ${addresses.escrowProxy}`);
  console.log(`   Multi-Sig: ${addresses.multiSig}`);
  console.log("");

  try {
    // Get current implementation details
    console.log("📊 Current Implementation Status:");
    const currentImplementation = await upgrades.erc1967.getImplementationAddress(addresses.escrowProxy);
    console.log(`   Current Implementation: ${currentImplementation}`);
    
    const SmartEscrowUpgradeable = await ethers.getContractFactory("SmartEscrowUpgradeable");
    const currentContract = SmartEscrowUpgradeable.attach(addresses.escrowProxy);
    const currentVersion = await currentContract.getVersion();
    console.log(`   Current Version: ${currentVersion}`);
    console.log("");

    // Step 1: Validate upgrade compatibility
    const isValid = await validateUpgrade(addresses.escrowProxy, SmartEscrowUpgradeable);
    if (!isValid) {
      throw new Error("Upgrade validation failed");
    }
    console.log("");

    // Step 2: Prepare new implementation
    const newImplementationAddress = await prepareUpgrade(addresses.escrowProxy, SmartEscrowUpgradeable);
    console.log("");

    // Step 3: Create upgrade proposal for multi-sig
    const transactionId = await createUpgradeProposal(
      addresses.multiSig,
      addresses.escrowProxy,
      newImplementationAddress
    );
    console.log("");

    // Step 4: Check proposal status
    const status = await checkUpgradeStatus(addresses.multiSig, transactionId);
    console.log("");

    console.log("🎉 Upgrade Process Summary");
    console.log("==========================");
    console.log(`Network: ${network}`);
    console.log(`Current Implementation: ${currentImplementation}`);
    console.log(`New Implementation: ${newImplementationAddress}`);
    console.log(`Multi-sig Transaction ID: ${transactionId}`);
    console.log(`Confirmations Needed: ${status.required}`);
    console.log("");
    
    console.log("📋 Next Steps:");
    console.log("1. Multi-sig owners need to confirm the upgrade transaction");
    console.log("2. Once confirmed, execute the upgrade transaction");
    console.log("3. Verify the upgrade was successful");
    console.log("4. Test the upgraded contract functionality");
    console.log("");
    
    console.log("🔧 Commands for Multi-sig Owners:");
    console.log(`   Confirm: multiSig.confirmTransaction(${transactionId})`);
    console.log(`   Execute: multiSig.executeTransaction(${transactionId})`);
    console.log("");

    return {
      network,
      currentImplementation,
      newImplementation: newImplementationAddress,
      transactionId,
      status
    };

  } catch (error) {
    console.error("❌ Upgrade process failed:");
    console.error(error);
    throw error;
  }
}

// Execute upgrade if this script is run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main()
    .then((result) => {
      console.log("✅ Upgrade process completed!");
      console.log("Result:", JSON.stringify(result, null, 2));
      process.exit(0);
    })
    .catch((error) => {
      console.error("❌ Upgrade process failed:");
      console.error(error);
      process.exit(1);
    });
}

export default main;