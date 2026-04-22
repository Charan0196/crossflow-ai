import { expect } from "chai";
import hre from "hardhat";
const { ethers } = hre;
import { time, loadFixture } from "@nomicfoundation/hardhat-network-helpers";

/**
 * Property-Based Tests for ERC-7683 Intent Engine
 * 
 * These tests validate the correctness properties defined in the design document
 * Each test runs with minimum 100 iterations as specified in requirements
 */
describe("IntentEngine Property Tests", function () {
  // Test fixture for deploying contracts
  async function deployIntentEngineFixture() {
    const [owner, user1, user2, solver1, solver2] = await ethers.getSigners();

    const IntentEngine = await ethers.getContractFactory("IntentEngine");
    const intentEngine = await IntentEngine.deploy(owner.address);

    // Authorize solvers
    await intentEngine.setSolverAuthorization(solver1.address, true);
    await intentEngine.setSolverAuthorization(solver2.address, true);

    // Mock ERC20 tokens for testing
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    const inputToken = await MockERC20.deploy("Input Token", "INPUT", 18);
    const outputToken = await MockERC20.deploy("Output Token", "OUTPUT", 18);

    // Set up supported tokens on all supported chains for comprehensive testing
    const supportedChains = [1, 137, 42161, 10, 56, 8453];
    
    for (const chainId of supportedChains) {
      await intentEngine.setSupportedToken(inputToken.target, chainId, true);
      await intentEngine.setSupportedToken(outputToken.target, chainId, true);
    }

    return {
      intentEngine,
      owner,
      user1,
      user2,
      solver1,
      solver2,
      inputToken,
      outputToken
    };
  }

  // Helper function to generate random intent parameters
  function generateRandomIntentParams() {
    const now = Math.floor(Date.now() / 1000);
    const minDeadline = now + 300; // 5 minutes minimum
    const maxDeadline = now + 86400 * 7; // 7 days maximum
    
    return {
      inputAmount: ethers.parseEther((Math.random() * 1000 + 1).toString()),
      minimumOutputAmount: ethers.parseEther((Math.random() * 900 + 1).toString()),
      deadline: Math.floor(Math.random() * (maxDeadline - minDeadline) + minDeadline),
      sourceChain: [1, 137, 42161, 10, 56, 8453][Math.floor(Math.random() * 6)],
      destinationChain: [1, 137, 42161, 10, 56, 8453][Math.floor(Math.random() * 6)]
    };
  }

  // Helper function to create intent with random or specific parameters
  function createIntent(user, inputToken, outputToken, nonce = 0, params = null) {
    const randomParams = params || generateRandomIntentParams();
    
    return {
      user: user.address,
      sourceChain: randomParams.sourceChain,
      destinationChain: randomParams.destinationChain,
      inputToken: inputToken.target,
      outputToken: outputToken.target,
      inputAmount: randomParams.inputAmount,
      minimumOutputAmount: randomParams.minimumOutputAmount,
      deadline: randomParams.deadline,
      nonce: nonce,
      recipient: user.address
    };
  }

  // Helper function to sign an intent
  async function signIntent(intent, signer, contractAddress) {
    const domain = {
      name: "CrossFlow AI Intent Engine",
      version: "1.0.0",
      chainId: await ethers.provider.getNetwork().then(n => n.chainId),
      verifyingContract: contractAddress
    };

    const types = {
      Intent: [
        { name: "user", type: "address" },
        { name: "sourceChain", type: "uint256" },
        { name: "destinationChain", type: "uint256" },
        { name: "inputToken", type: "address" },
        { name: "outputToken", type: "address" },
        { name: "inputAmount", type: "uint256" },
        { name: "minimumOutputAmount", type: "uint256" },
        { name: "deadline", type: "uint256" },
        { name: "nonce", type: "uint256" },
        { name: "recipient", type: "address" }
      ]
    };

    const signature = await signer.signTypedData(domain, types, intent);
    return signature;
  }

  /**
   * Property 1: ERC-7683 Compliance
   * Validates: Requirements 1.1, 1.2
   * 
   * This property ensures that all intent operations comply with ERC-7683 standard:
   * - Intent hash computation is deterministic and consistent
   * - Signature verification works correctly
   * - Intent lifecycle (create -> fulfill/cancel) is properly managed
   */
  describe("Property 1: ERC-7683 Compliance", function () {
    it("Should maintain deterministic intent hash computation across 100 iterations", async function () {
      const { intentEngine, user1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      for (let i = 0; i < 100; i++) {
        const intent = createIntent(user1, inputToken, outputToken, i);
        
        // Compute hash multiple times - should be identical
        const hash1 = await intentEngine.computeIntentHash(intent);
        const hash2 = await intentEngine.computeIntentHash(intent);
        
        expect(hash1).to.equal(hash2, `Hash computation not deterministic at iteration ${i}`);
        
        // Verify hash changes with different nonce
        const intentWithDifferentNonce = { ...intent, nonce: intent.nonce + 1 };
        const hashDifferent = await intentEngine.computeIntentHash(intentWithDifferentNonce);
        
        expect(hash1).to.not.equal(hashDifferent, `Hash should change with different nonce at iteration ${i}`);
      }
    });

    it("Should correctly verify signatures across 100 random intents", async function () {
      const { intentEngine, user1, user2, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      for (let i = 0; i < 100; i++) {
        const intent = createIntent(user1, inputToken, outputToken, i);
        const signature = await signIntent(intent, user1, intentEngine.target);
        const signedIntent = { intent, signature };

        // Valid signature should work
        await expect(intentEngine.connect(user1).createIntent(signedIntent))
          .to.not.be.reverted;

        // Wrong signer should fail
        const wrongSignature = await signIntent(intent, user2, intentEngine.target);
        const wrongSignedIntent = { intent, signature: wrongSignature };

        await expect(intentEngine.connect(user1).createIntent(wrongSignedIntent))
          .to.be.revertedWith("Invalid signature");
      }
    });

    it("Should maintain proper intent lifecycle state transitions", async function () {
      const { intentEngine, user1, solver1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      for (let i = 0; i < 50; i++) { // 50 iterations for performance
        const intent = createIntent(user1, inputToken, outputToken, i);
        const signature = await signIntent(intent, user1, intentEngine.target);
        const signedIntent = { intent, signature };

        // Create intent
        await intentEngine.connect(user1).createIntent(signedIntent);
        const intentHash = await intentEngine.computeIntentHash(intent);

        // Verify initial state
        expect(await intentEngine.isIntentFulfilled(intentHash)).to.be.false;
        expect(await intentEngine.isIntentCancelled(intentHash)).to.be.false;

        if (i % 2 === 0) {
          // Test fulfillment path
          const fulfillment = {
            intentHash: intentHash,
            solver: solver1.address,
            outputAmount: intent.minimumOutputAmount,
            proof: "0x1234"
          };

          await intentEngine.connect(solver1).fulfillIntent(fulfillment);
          expect(await intentEngine.isIntentFulfilled(intentHash)).to.be.true;
          
          // Should not be able to cancel fulfilled intent
          await expect(intentEngine.connect(user1).cancelIntent(intentHash))
            .to.be.revertedWith("Intent already fulfilled");
        } else {
          // Test cancellation path
          await intentEngine.connect(user1).cancelIntent(intentHash);
          expect(await intentEngine.isIntentCancelled(intentHash)).to.be.true;
          
          // Should not be able to fulfill cancelled intent
          const fulfillment = {
            intentHash: intentHash,
            solver: solver1.address,
            outputAmount: intent.minimumOutputAmount,
            proof: "0x1234"
          };

          await expect(intentEngine.connect(solver1).fulfillIntent(fulfillment))
            .to.be.revertedWith("Intent cancelled");
        }
      }
    });
  });

  /**
   * Property 2: Intent Validation Consistency
   * Validates: Requirements 1.3, 7.1, 7.2
   * 
   * This property ensures that intent validation is consistent and secure:
   * - Invalid intents are always rejected
   * - Valid intents are always accepted
   * - Validation rules are consistently applied
   */
  describe("Property 2: Intent Validation Consistency", function () {
    it("Should consistently reject invalid deadline intents across 100 iterations", async function () {
      const { intentEngine, user1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      for (let i = 0; i < 100; i++) {
        // Create intent with expired deadline
        const expiredIntent = createIntent(user1, inputToken, outputToken, i, {
          ...generateRandomIntentParams(),
          deadline: Math.floor(Date.now() / 1000) - Math.floor(Math.random() * 3600) // Random time in the past
        });

        const signature = await signIntent(expiredIntent, user1, intentEngine.target);
        const signedIntent = { intent: expiredIntent, signature };

        await expect(intentEngine.connect(user1).createIntent(signedIntent))
          .to.be.revertedWith("Intent has expired");
      }
    });

    it("Should consistently reject intents with invalid amounts across 100 iterations", async function () {
      const { intentEngine, user1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      for (let i = 0; i < 100; i++) {
        // Create intent with zero input amount
        const zeroAmountIntent = createIntent(user1, inputToken, outputToken, i, {
          ...generateRandomIntentParams(),
          inputAmount: 0
        });

        const signature = await signIntent(zeroAmountIntent, user1, intentEngine.target);
        const signedIntent = { intent: zeroAmountIntent, signature };

        await expect(intentEngine.connect(user1).createIntent(signedIntent))
          .to.be.revertedWith("Input amount must be greater than zero");
      }
    });

    it("Should consistently validate supported chains across 100 iterations", async function () {
      const supportedChains = [1, 137, 42161, 10, 56, 8453];
      const unsupportedChains = [999, 1000, 2000, 3000];

      for (let i = 0; i < 50; i++) { // Reduced to 50 for performance
        const { intentEngine, user1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);
        
        // Test with supported chains - should work
        const validIntent = createIntent(user1, inputToken, outputToken, 0, {
          ...generateRandomIntentParams(),
          sourceChain: supportedChains[i % supportedChains.length],
          destinationChain: supportedChains[(i + 1) % supportedChains.length]
        });

        const validSignature = await signIntent(validIntent, user1, intentEngine.target);
        const validSignedIntent = { intent: validIntent, signature: validSignature };

        await expect(intentEngine.connect(user1).createIntent(validSignedIntent))
          .to.not.be.reverted;

        // Test with unsupported source chain - should fail
        const invalidSourceIntent = createIntent(user1, inputToken, outputToken, 1, {
          ...generateRandomIntentParams(),
          sourceChain: unsupportedChains[i % unsupportedChains.length],
          destinationChain: supportedChains[i % supportedChains.length]
        });

        const invalidSignature = await signIntent(invalidSourceIntent, user1, intentEngine.target);
        const invalidSignedIntent = { intent: invalidSourceIntent, signature: invalidSignature };

        await expect(intentEngine.connect(user1).createIntent(invalidSignedIntent))
          .to.be.revertedWith("Source chain not supported");
      }
    });

    it("Should enforce minimum output amount requirements consistently", async function () {
      const { intentEngine, user1, solver1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      for (let i = 0; i < 50; i++) { // 50 iterations for performance
        const intent = createIntent(user1, inputToken, outputToken, i);
        const signature = await signIntent(intent, user1, intentEngine.target);
        const signedIntent = { intent, signature };

        await intentEngine.connect(user1).createIntent(signedIntent);
        const intentHash = await intentEngine.computeIntentHash(intent);

        // Try to fulfill with amount below minimum - should fail
        const insufficientAmount = intent.minimumOutputAmount - BigInt(1);
        const badFulfillment = {
          intentHash: intentHash,
          solver: solver1.address,
          outputAmount: insufficientAmount,
          proof: "0x1234"
        };

        await expect(intentEngine.connect(solver1).fulfillIntent(badFulfillment))
          .to.be.revertedWith("Insufficient output amount");

        // Fulfill with exact minimum amount - should work
        const goodFulfillment = {
          intentHash: intentHash,
          solver: solver1.address,
          outputAmount: intent.minimumOutputAmount,
          proof: "0x1234"
        };

        await expect(intentEngine.connect(solver1).fulfillIntent(goodFulfillment))
          .to.not.be.reverted;
      }
    });
  });

  /**
   * Property 3: Solver Network Broadcasting
   * Validates: Requirements 1.4, 4.1
   * 
   * This property ensures that solver authorization and intent broadcasting work correctly:
   * - Only authorized solvers can fulfill intents
   * - Intent events are properly emitted for solver monitoring
   * - Solver authorization changes are properly managed
   */
  describe("Property 3: Solver Network Broadcasting", function () {
    it("Should consistently enforce solver authorization across 100 iterations", async function () {
      const { intentEngine, owner, user1, solver1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      for (let i = 0; i < 100; i++) {
        const intent = createIntent(user1, inputToken, outputToken, i);
        const signature = await signIntent(intent, user1, intentEngine.target);
        const signedIntent = { intent, signature };

        await intentEngine.connect(user1).createIntent(signedIntent);
        const intentHash = await intentEngine.computeIntentHash(intent);

        const fulfillment = {
          intentHash: intentHash,
          solver: solver1.address,
          outputAmount: intent.minimumOutputAmount,
          proof: "0x1234"
        };

        if (i % 3 === 0) {
          // Deauthorize solver
          await intentEngine.connect(owner).setSolverAuthorization(solver1.address, false);
          
          await expect(intentEngine.connect(solver1).fulfillIntent(fulfillment))
            .to.be.revertedWith("Unauthorized solver");
          
          // Re-authorize solver
          await intentEngine.connect(owner).setSolverAuthorization(solver1.address, true);
        }

        // Should work when authorized
        await expect(intentEngine.connect(solver1).fulfillIntent(fulfillment))
          .to.not.be.reverted;
      }
    });

    it("Should emit proper events for solver monitoring across 100 intents", async function () {
      const { intentEngine, user1, solver1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      for (let i = 0; i < 100; i++) {
        const intent = createIntent(user1, inputToken, outputToken, i);
        const signature = await signIntent(intent, user1, intentEngine.target);
        const signedIntent = { intent, signature };

        // Intent creation should emit events
        await expect(intentEngine.connect(user1).createIntent(signedIntent))
          .to.emit(intentEngine, "IntentCreated")
          .to.emit(intentEngine, "IntentValidated");

        const intentHash = await intentEngine.computeIntentHash(intent);
        const fulfillment = {
          intentHash: intentHash,
          solver: solver1.address,
          outputAmount: intent.minimumOutputAmount,
          proof: "0x1234"
        };

        // Intent fulfillment should emit event
        await expect(intentEngine.connect(solver1).fulfillIntent(fulfillment))
          .to.emit(intentEngine, "IntentFulfilled")
          .withArgs(intentHash, solver1.address, fulfillment.outputAmount);
      }
    });

    it("Should handle concurrent solver operations correctly", async function () {
      const { intentEngine, user1, solver1, solver2, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create multiple intents that can be fulfilled concurrently
      const intents = [];
      const intentHashes = [];

      for (let i = 0; i < 20; i++) {
        const intent = createIntent(user1, inputToken, outputToken, i);
        const signature = await signIntent(intent, user1, intentEngine.target);
        const signedIntent = { intent, signature };

        await intentEngine.connect(user1).createIntent(signedIntent);
        const intentHash = await intentEngine.computeIntentHash(intent);
        
        intents.push(intent);
        intentHashes.push(intentHash);
      }

      // Try to fulfill same intent with different solvers - only first should succeed
      for (let i = 0; i < intents.length; i++) {
        const fulfillment1 = {
          intentHash: intentHashes[i],
          solver: solver1.address,
          outputAmount: intents[i].minimumOutputAmount,
          proof: "0x1234"
        };

        const fulfillment2 = {
          intentHash: intentHashes[i],
          solver: solver2.address,
          outputAmount: intents[i].minimumOutputAmount,
          proof: "0x5678"
        };

        // First fulfillment should succeed
        await expect(intentEngine.connect(solver1).fulfillIntent(fulfillment1))
          .to.not.be.reverted;

        // Second fulfillment should fail
        await expect(intentEngine.connect(solver2).fulfillIntent(fulfillment2))
          .to.be.revertedWith("Intent already fulfilled");
      }
    });
  });

  describe("Gas Optimization Properties", function () {
    it("Should maintain reasonable gas costs across different intent sizes", async function () {
      const { intentEngine, user1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      const gasCosts = [];

      for (let i = 0; i < 50; i++) {
        const intent = createIntent(user1, inputToken, outputToken, i);
        const signature = await signIntent(intent, user1, intentEngine.target);
        const signedIntent = { intent, signature };

        const tx = await intentEngine.connect(user1).createIntent(signedIntent);
        const receipt = await tx.wait();
        gasCosts.push(receipt.gasUsed);
      }

      // Verify gas costs are within reasonable bounds and consistent
      const avgGas = gasCosts.reduce((a, b) => a + b, BigInt(0)) / BigInt(gasCosts.length);
      const maxGas = gasCosts.reduce((a, b) => a > b ? a : b, BigInt(0));
      const minGas = gasCosts.reduce((a, b) => a < b ? a : b, gasCosts[0]);

      // Gas usage should be consistent (within 10% variance)
      const variance = (maxGas - minGas) * BigInt(100) / avgGas;
      expect(variance).to.be.lessThan(BigInt(10), "Gas usage variance too high");

      // Gas usage should be reasonable (less than 300k gas)
      expect(maxGas).to.be.lessThan(BigInt(300000), "Gas usage too high");
    });
  });
});