import hre from "hardhat";
const { ethers, upgrades } = hre;

/**
 * CrossFlow AI Phase 1 - Smart Escrow Deployment Script
 * Deploys SmartEscrowUpgradeable with multi-signature governance and proxy patterns
 */

// Configuration for different networks
const NETWORK_CONFIG = {
  localhost: {
    name: "Localhost",
    chainId: 31337,
    governanceMembers: [
      "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266", // Hardhat account #0
      "0x70997970C51812dc3A010C7d01b50e0d17dc79C8", // Hardhat account #1
      "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC", // Hardhat account #2
    ],
    governanceThreshold: 2, // 2 out of 3 signatures required
    verificationDelay: 30, // 30 seconds for testing
  },
  ethereum: {
    name: "Ethereum Mainnet",
    chainId: 1,
    governanceMembers: [
      // Add actual governance member addresses here
      "0x742d35Cc6634C0532925a3b8D4C9db96c4b4d8b6", // Example address 1
      "0x8ba1f109551bD432803012645Hac136c22C177ec", // Example address 2
      "0x1234567890123456789012345678901234567890", // Example address 3
    ],
    governanceThreshold: 2, // 2 out of 3 signatures required
    verificationDelay: 300, // 5 minutes delay for verification
  },
  arbitrum: {
    name: "Arbitrum One",
    chainId: 42161,
    governanceMembers: [
      // Add actual governance member addresses here
      "0x742d35Cc6634C0532925a3b8D4C9db96c4b4d8b6", // Example address 1
      "0x8ba1f109551bD432803012645Hac136c22C177ec", // Example address 2
      "0x1234567890123456789012345678901234567890", // Example address 3
    ],
    governanceThreshold: 2, // 2 out of 3 signatures required
    verificationDelay: 60, // 1 minute delay for verification (faster on L2)
  },
  sepolia: {
    name: "Sepolia Testnet",
    chainId: 11155111,
    governanceMembers: [
      "0x742d35Cc6634C0532925a3b8D4C9db96c4b4d8b6", // Test address 1
      "0x8ba1f109551bD432803012645Hac136c22C177ec", // Test address 2
    ],
    governanceThreshold: 1, // 1 out of 2 for testing
    verificationDelay: 30, // 30 seconds for testing
  },
  arbitrumSepolia: {
    name: "Arbitrum Sepolia",
    chainId: 421614,
    governanceMembers: [
      "0x742d35Cc6634C0532925a3b8D4C9db96c4b4d8b6", // Test address 1
      "0x8ba1f109551bD432803012645Hac136c22C177ec", // Test address 2
    ],
    governanceThreshold: 1, // 1 out of 2 for testing
    verificationDelay: 30, // 30 seconds for testing
  },
};

async function deployMultiSigWallet(config) {
  console.log("📋 Deploying Multi-Signature Wallet...");
  
  const MultiSigWallet = await ethers.getContractFactory("MultiSigWallet");
  const multiSigWallet = await MultiSigWallet.deploy(
    config.governanceMembers,
    config.governanceThreshold
  );
  
  await multiSigWallet.waitForDeployment();
  const multiSigAddress = await multiSigWallet.getAddress();
  
  console.log(`✅ MultiSigWallet deployed to: ${multiSigAddress}`);
  console.log(`   Governance Members: ${config.governanceMembers.length}`);
  console.log(`   Required Signatures: ${config.governanceThreshold}`);
  
  return { multiSigWallet, multiSigAddress };
}

async function deploySmartEscrow(config, multiSigAddress) {
  console.log("🔒 Deploying Smart Escrow with Proxy Pattern...");
  
  const SmartEscrowUpgradeable = await ethers.getContractFactory("SmartEscrowUpgradeable");
  
  // Deploy using OpenZeppelin upgrades plugin
  const smartEscrow = await upgrades.deployProxy(
    SmartEscrowUpgradeable,
    [
      multiSigAddress, // Initial owner (multi-sig wallet)
      config.governanceMembers,
      config.governanceThreshold
    ],
    {
      initializer: "initialize",
      kind: "uups", // Use UUPS proxy pattern
    }
  );
  
  await smartEscrow.waitForDeployment();
  const escrowAddress = await smartEscrow.getAddress();
  
  console.log(`✅ SmartEscrowUpgradeable deployed to: ${escrowAddress}`);
  console.log(`   Proxy Pattern: UUPS`);
  console.log(`   Owner: ${multiSigAddress} (MultiSig)`);
  
  // Get implementation address
  const implementationAddress = await upgrades.erc1967.getImplementationAddress(escrowAddress);
  console.log(`   Implementation: ${implementationAddress}`);
  
  return { smartEscrow, escrowAddress, implementationAddress };
}

async function setupInitialConfiguration(smartEscrow, config) {
  console.log("⚙️  Setting up initial configuration...");
  
  try {
    // Verify initial configuration
    const timeoutPeriod = await smartEscrow.timeoutPeriod();
    const governanceThreshold = await smartEscrow.governanceThreshold();
    const governanceMemberCount = await smartEscrow.governanceMemberCount();
    
    console.log(`   Timeout Period: ${timeoutPeriod} seconds (${timeoutPeriod / 60} minutes)`);
    console.log(`   Governance Threshold: ${governanceThreshold}`);
    console.log(`   Governance Members: ${governanceMemberCount}`);
    
    // Verify governance members
    for (let i = 0; i < config.governanceMembers.length; i++) {
      const isMember = await smartEscrow.governanceMembers(config.governanceMembers[i]);
      console.log(`   Member ${i + 1}: ${config.governanceMembers[i]} - ${isMember ? "✅" : "❌"}`);
    }
    
    console.log("✅ Initial configuration verified");
    
  } catch (error) {
    console.error("❌ Error setting up initial configuration:", error.message);
    throw error;
  }
}

async function verifyContracts(addresses, config) {
  console.log("🔍 Contract verification will be available after deployment...");
  
  // Note: Actual verification would be done separately using:
  // npx hardhat verify --network <network> <address> <constructor-args>
  
  console.log("📝 Verification Commands:");
  console.log(`   MultiSig: npx hardhat verify --network ${hre.network.name} ${addresses.multiSigAddress} '${JSON.stringify(config.governanceMembers)}' ${config.governanceThreshold}`);
  console.log(`   Escrow Implementation: npx hardhat verify --network ${hre.network.name} ${addresses.implementationAddress}`);
  console.log(`   Note: Proxy contracts are automatically verified by OpenZeppelin`);
}

async function setupMonitoring(addresses, config) {
  console.log("📊 Setting up monitoring and alerts...");
  
  // This would integrate with monitoring services like Defender, Tenderly, etc.
  console.log("📋 Monitoring Setup:");
  console.log(`   - Smart Escrow Proxy: ${addresses.escrowAddress}`);
  console.log(`   - Multi-Sig Wallet: ${addresses.multiSigAddress}`);
  console.log(`   - Implementation: ${addresses.implementationAddress}`);
  console.log(`   - Network: ${config.name} (Chain ID: ${config.chainId})`);
  
  // Recommended monitoring alerts:
  console.log("\n🚨 Recommended Monitoring Alerts:");
  console.log("   - Large fund locks (> $100k)");
  console.log("   - Failed transactions");
  console.log("   - Governance proposal submissions");
  console.log("   - Emergency pause events");
  console.log("   - Upgrade proposals");
  console.log("   - Unusual solver activity");
}

async function main() {
  console.log("🚀 CrossFlow AI Phase 1 - Smart Escrow Deployment");
  console.log("==================================================");
  
  const [deployer] = await ethers.getSigners();
  const network = hre.network.name;
  const chainId = hre.network.config.chainId;
  
  console.log(`Network: ${network} (Chain ID: ${chainId})`);
  console.log(`Deployer: ${deployer.address}`);
  console.log(`Balance: ${ethers.formatEther(await ethers.provider.getBalance(deployer.address))} ETH`);
  console.log("");

  // Get network configuration
  const config = NETWORK_CONFIG[network];
  if (!config) {
    throw new Error(`Network configuration not found for: ${network}`);
  }
  
  console.log(`📋 Network Configuration: ${config.name}`);
  console.log(`   Governance Members: ${config.governanceMembers.length}`);
  console.log(`   Required Signatures: ${config.governanceThreshold}`);
  console.log(`   Verification Delay: ${config.verificationDelay} seconds`);
  console.log("");

  try {
    // Step 1: Deploy Multi-Signature Wallet
    const { multiSigWallet, multiSigAddress } = await deployMultiSigWallet(config);
    console.log("");

    // Step 2: Deploy Smart Escrow with Proxy Pattern
    const { smartEscrow, escrowAddress, implementationAddress } = await deploySmartEscrow(config, multiSigAddress);
    console.log("");

    // Step 3: Setup Initial Configuration
    await setupInitialConfiguration(smartEscrow, config);
    console.log("");

    // Step 4: Prepare Contract Verification
    const addresses = {
      multiSigAddress,
      escrowAddress,
      implementationAddress
    };
    await verifyContracts(addresses, config);
    console.log("");

    // Step 5: Setup Monitoring
    await setupMonitoring(addresses, config);
    console.log("");

    // Step 6: Final Summary
    console.log("🎉 Deployment Summary");
    console.log("====================");
    console.log(`Network: ${config.name} (${network})`);
    console.log(`Multi-Sig Wallet: ${multiSigAddress}`);
    console.log(`Smart Escrow Proxy: ${escrowAddress}`);
    console.log(`Implementation: ${implementationAddress}`);
    console.log("");
    
    console.log("📋 Next Steps:");
    console.log("1. Verify contracts on block explorer");
    console.log("2. Set up monitoring alerts");
    console.log("3. Configure solver authorizations");
    console.log("4. Test with small amounts first");
    console.log("5. Gradually increase limits");
    console.log("");
    
    console.log("⚠️  Security Reminders:");
    console.log("- Multi-sig wallet controls all upgrades");
    console.log("- Test all governance functions");
    console.log("- Monitor for unusual activity");
    console.log("- Keep private keys secure");
    console.log("");

    return {
      network: config.name,
      chainId: config.chainId,
      multiSigWallet: multiSigAddress,
      smartEscrow: escrowAddress,
      implementation: implementationAddress,
      governanceMembers: config.governanceMembers,
      governanceThreshold: config.governanceThreshold
    };

  } catch (error) {
    console.error("❌ Deployment failed:");
    console.error(error);
    throw error;
  }
}

// Execute deployment if this script is run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main()
    .then((result) => {
      console.log("✅ Deployment completed successfully!");
      console.log("Result:", JSON.stringify(result, null, 2));
      process.exit(0);
    })
    .catch((error) => {
      console.error("❌ Deployment failed:");
      console.error(error);
      process.exit(1);
    });
}

export default main;