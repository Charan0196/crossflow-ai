import hre from "hardhat";
const { ethers } = hre;

/**
 * CrossFlow AI Phase 1 - Smart Escrow Monitoring Script
 * Monitors contract health, governance activities, and system metrics
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

async function checkContractHealth(escrowAddress) {
  console.log("🏥 Checking Contract Health...");
  
  try {
    const SmartEscrowUpgradeable = await ethers.getContractFactory("SmartEscrowUpgradeable");
    const escrow = SmartEscrowUpgradeable.attach(escrowAddress);
    
    // Basic contract status
    const isPaused = await escrow.paused();
    const owner = await escrow.owner();
    const version = await escrow.getVersion();
    const timeoutPeriod = await escrow.timeoutPeriod();
    
    console.log(`   Contract Status: ${isPaused ? "⏸️  PAUSED" : "✅ ACTIVE"}`);
    console.log(`   Owner: ${owner}`);
    console.log(`   Version: ${version}`);
    console.log(`   Timeout Period: ${timeoutPeriod} seconds (${timeoutPeriod / 60} minutes)`);
    
    // Governance status
    const governanceThreshold = await escrow.governanceThreshold();
    const governanceMemberCount = await escrow.governanceMemberCount();
    
    console.log(`   Governance Threshold: ${governanceThreshold}`);
    console.log(`   Governance Members: ${governanceMemberCount}`);
    
    return {
      isPaused,
      owner,
      version: Number(version),
      timeoutPeriod: Number(timeoutPeriod),
      governanceThreshold: Number(governanceThreshold),
      governanceMemberCount: Number(governanceMemberCount)
    };
  } catch (error) {
    console.error("❌ Error checking contract health:", error.message);
    throw error;
  }
}

async function checkMultiSigStatus(multiSigAddress) {
  console.log("🔐 Checking Multi-Sig Wallet Status...");
  
  try {
    const MultiSigWallet = await ethers.getContractFactory("MultiSigWallet");
    const multiSig = MultiSigWallet.attach(multiSigAddress);
    
    // Basic multi-sig info
    const owners = await multiSig.getOwners();
    const required = await multiSig.required();
    const balance = await ethers.provider.getBalance(multiSigAddress);
    
    console.log(`   Owners: ${owners.length}`);
    console.log(`   Required Signatures: ${required}`);
    console.log(`   Balance: ${ethers.formatEther(balance)} ETH`);
    
    // Pending transactions
    const pendingCount = await multiSig.getTransactionCount(true, false);
    const executedCount = await multiSig.getTransactionCount(false, true);
    
    console.log(`   Pending Transactions: ${pendingCount}`);
    console.log(`   Executed Transactions: ${executedCount}`);
    
    // List owners
    console.log("   Owners:");
    owners.forEach((owner, index) => {
      console.log(`     ${index + 1}. ${owner}`);
    });
    
    return {
      owners,
      required: Number(required),
      balance: ethers.formatEther(balance),
      pendingCount: Number(pendingCount),
      executedCount: Number(executedCount)
    };
  } catch (error) {
    console.error("❌ Error checking multi-sig status:", error.message);
    throw error;
  }
}

async function getRecentEvents(escrowAddress, fromBlock = -1000) {
  console.log("📊 Fetching Recent Events...");
  
  try {
    const SmartEscrowUpgradeable = await ethers.getContractFactory("SmartEscrowUpgradeable");
    const escrow = SmartEscrowUpgradeable.attach(escrowAddress);
    
    const currentBlock = await ethers.provider.getBlockNumber();
    const startBlock = Math.max(0, currentBlock + fromBlock);
    
    console.log(`   Scanning blocks ${startBlock} to ${currentBlock}`);
    
    // Get all events
    const events = await escrow.queryFilter("*", startBlock, currentBlock);
    
    console.log(`   Found ${events.length} events`);
    
    // Categorize events
    const eventSummary = {};
    events.forEach(event => {
      const eventName = event.fragment?.name || "Unknown";
      eventSummary[eventName] = (eventSummary[eventName] || 0) + 1;
    });
    
    console.log("   Event Summary:");
    Object.entries(eventSummary).forEach(([eventName, count]) => {
      console.log(`     ${eventName}: ${count}`);
    });
    
    // Show recent critical events
    const criticalEvents = events.filter(event => {
      const name = event.fragment?.name;
      return ["FundsLocked", "FundsReleased", "FundsRefunded", "EmergencyWithdrawal", "ContractUpgraded"].includes(name);
    });
    
    if (criticalEvents.length > 0) {
      console.log("   Recent Critical Events:");
      criticalEvents.slice(-5).forEach(event => {
        console.log(`     ${event.fragment.name} - Block ${event.blockNumber}`);
      });
    }
    
    return {
      totalEvents: events.length,
      eventSummary,
      criticalEvents: criticalEvents.length
    };
  } catch (error) {
    console.error("❌ Error fetching events:", error.message);
    throw error;
  }
}

async function checkSolverAuthorizations(escrowAddress) {
  console.log("🤖 Checking Solver Authorizations...");
  
  try {
    const SmartEscrowUpgradeable = await ethers.getContractFactory("SmartEscrowUpgradeable");
    const escrow = SmartEscrowUpgradeable.attach(escrowAddress);
    
    // Get SolverAuthorized events to find all solvers
    const events = await escrow.queryFilter("SolverAuthorized", -10000);
    
    const solvers = new Map();
    events.forEach(event => {
      const solver = event.args[0];
      const authorized = event.args[1];
      solvers.set(solver, authorized);
    });
    
    console.log(`   Total Solvers Configured: ${solvers.size}`);
    
    const authorizedSolvers = [];
    const deauthorizedSolvers = [];
    
    for (const [solver, authorized] of solvers.entries()) {
      if (authorized) {
        authorizedSolvers.push(solver);
      } else {
        deauthorizedSolvers.push(solver);
      }
    }
    
    console.log(`   Authorized Solvers: ${authorizedSolvers.length}`);
    authorizedSolvers.forEach((solver, index) => {
      console.log(`     ${index + 1}. ${solver}`);
    });
    
    if (deauthorizedSolvers.length > 0) {
      console.log(`   Deauthorized Solvers: ${deauthorizedSolvers.length}`);
    }
    
    return {
      totalSolvers: solvers.size,
      authorizedCount: authorizedSolvers.length,
      deauthorizedCount: deauthorizedSolvers.length,
      authorizedSolvers,
      deauthorizedSolvers
    };
  } catch (error) {
    console.error("❌ Error checking solver authorizations:", error.message);
    throw error;
  }
}

async function generateHealthReport(escrowAddress, multiSigAddress) {
  console.log("📋 Generating Health Report...");
  
  const timestamp = new Date().toISOString();
  const network = hre.network.name;
  
  try {
    const contractHealth = await checkContractHealth(escrowAddress);
    const multiSigStatus = await checkMultiSigStatus(multiSigAddress);
    const eventData = await getRecentEvents(escrowAddress);
    const solverData = await checkSolverAuthorizations(escrowAddress);
    
    const report = {
      timestamp,
      network,
      addresses: {
        escrow: escrowAddress,
        multiSig: multiSigAddress
      },
      contractHealth,
      multiSigStatus,
      eventData,
      solverData,
      alerts: []
    };
    
    // Generate alerts based on health checks
    if (contractHealth.isPaused) {
      report.alerts.push("🚨 CONTRACT IS PAUSED");
    }
    
    if (multiSigStatus.pendingCount > 5) {
      report.alerts.push(`⚠️  High number of pending multi-sig transactions: ${multiSigStatus.pendingCount}`);
    }
    
    if (solverData.authorizedCount === 0) {
      report.alerts.push("⚠️  No authorized solvers found");
    }
    
    if (eventData.criticalEvents > 10) {
      report.alerts.push(`⚠️  High number of critical events: ${eventData.criticalEvents}`);
    }
    
    console.log("\n📊 HEALTH REPORT SUMMARY");
    console.log("========================");
    console.log(`Timestamp: ${timestamp}`);
    console.log(`Network: ${network}`);
    console.log(`Contract Status: ${contractHealth.isPaused ? "PAUSED" : "ACTIVE"}`);
    console.log(`Authorized Solvers: ${solverData.authorizedCount}`);
    console.log(`Pending Multi-sig Txs: ${multiSigStatus.pendingCount}`);
    console.log(`Recent Events: ${eventData.totalEvents}`);
    
    if (report.alerts.length > 0) {
      console.log("\n🚨 ALERTS:");
      report.alerts.forEach(alert => console.log(`   ${alert}`));
    } else {
      console.log("\n✅ No alerts - System healthy");
    }
    
    return report;
  } catch (error) {
    console.error("❌ Error generating health report:", error.message);
    throw error;
  }
}

async function main() {
  console.log("📊 CrossFlow AI Phase 1 - Smart Escrow Monitoring");
  console.log("==================================================");
  
  const network = hre.network.name;
  console.log(`Network: ${network}`);
  console.log("");

  // Get deployed addresses for current network
  const addresses = DEPLOYED_ADDRESSES[network];
  if (!addresses || !addresses.escrowProxy) {
    throw new Error(`No deployed addresses found for network: ${network}. Please update DEPLOYED_ADDRESSES in the script.`);
  }
  
  console.log(`📋 Monitoring Contracts:`);
  console.log(`   Escrow Proxy: ${addresses.escrowProxy}`);
  console.log(`   Multi-Sig: ${addresses.multiSig}`);
  console.log("");

  try {
    // Run all health checks
    await checkContractHealth(addresses.escrowProxy);
    console.log("");
    
    await checkMultiSigStatus(addresses.multiSig);
    console.log("");
    
    await getRecentEvents(addresses.escrowProxy);
    console.log("");
    
    await checkSolverAuthorizations(addresses.escrowProxy);
    console.log("");
    
    // Generate comprehensive report
    const report = await generateHealthReport(addresses.escrowProxy, addresses.multiSig);
    
    return report;

  } catch (error) {
    console.error("❌ Monitoring failed:");
    console.error(error);
    throw error;
  }
}

// Execute monitoring if this script is run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main()
    .then((report) => {
      console.log("\n✅ Monitoring completed successfully!");
      // Optionally save report to file
      // fs.writeFileSync(`monitoring-report-${Date.now()}.json`, JSON.stringify(report, null, 2));
      process.exit(0);
    })
    .catch((error) => {
      console.error("❌ Monitoring failed:");
      console.error(error);
      process.exit(1);
    });
}

export default main;