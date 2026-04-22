import { expect } from "chai";
import hre from "hardhat";
const { ethers } = hre;
import { time, loadFixture } from "@nomicfoundation/hardhat-network-helpers";

describe("IntentEngine", function () {
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

    // Set up supported tokens on their respective chains
    await intentEngine.setSupportedToken(inputToken.target, 1, true); // Input token on Ethereum
    await intentEngine.setSupportedToken(outputToken.target, 137, true); // Output token on Polygon

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

  // Helper function to create a valid intent
  function createValidIntent(user, inputToken, outputToken, nonce = 0) {
    const deadline = Math.floor(Date.now() / 1000) + 3600; // 1 hour from now
    
    return {
      user: user.address,
      sourceChain: 1, // Ethereum
      destinationChain: 137, // Polygon
      inputToken: inputToken.target,
      outputToken: outputToken.target,
      inputAmount: ethers.parseEther("100"),
      minimumOutputAmount: ethers.parseEther("95"),
      deadline: deadline,
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

  describe("Deployment", function () {
    it("Should deploy with correct initial state", async function () {
      const { intentEngine, owner } = await loadFixture(deployIntentEngineFixture);

      expect(await intentEngine.owner()).to.equal(owner.address);
      expect(await intentEngine.NAME()).to.equal("CrossFlow AI Intent Engine");
      expect(await intentEngine.VERSION()).to.equal("1.0.0");
      
      // Check validation config
      const config = await intentEngine.getValidationConfig();
      expect(config.minimumDeadline).to.equal(300);
      expect(config.maximumDeadline).to.equal(86400 * 7);
    });

    it("Should initialize supported chains", async function () {
      const { intentEngine } = await loadFixture(deployIntentEngineFixture);

      expect(await intentEngine.isChainSupported(1)).to.be.true; // Ethereum
      expect(await intentEngine.isChainSupported(137)).to.be.true; // Polygon
      expect(await intentEngine.isChainSupported(42161)).to.be.true; // Arbitrum
      expect(await intentEngine.isChainSupported(10)).to.be.true; // Optimism
      expect(await intentEngine.isChainSupported(56)).to.be.true; // BSC
      expect(await intentEngine.isChainSupported(8453)).to.be.true; // Base
    });
  });

  describe("Intent Creation", function () {
    it("Should create a valid intent", async function () {
      const { intentEngine, user1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      const intent = createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user1, intentEngine.target);

      const signedIntent = { intent, signature };

      await expect(intentEngine.connect(user1).createIntent(signedIntent))
        .to.emit(intentEngine, "IntentCreated")
        .to.emit(intentEngine, "IntentValidated");

      const intentHash = await intentEngine.computeIntentHash(intent);
      const storedIntent = await intentEngine.getIntent(intentHash);
      
      expect(storedIntent.user).to.equal(intent.user);
      expect(storedIntent.inputAmount).to.equal(intent.inputAmount);
      expect(await intentEngine.getUserNonce(user1.address)).to.equal(1);
    });

    it("Should reject intent with invalid signature", async function () {
      const { intentEngine, user1, user2, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      const intent = createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user2, intentEngine.target); // Wrong signer

      const signedIntent = { intent, signature };

      await expect(intentEngine.connect(user1).createIntent(signedIntent))
        .to.be.revertedWith("Invalid signature");
    });

    it("Should reject intent with expired deadline", async function () {
      const { intentEngine, user1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      const intent = createValidIntent(user1, inputToken, outputToken);
      intent.deadline = Math.floor(Date.now() / 1000) - 3600; // 1 hour ago

      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      await expect(intentEngine.connect(user1).createIntent(signedIntent))
        .to.be.revertedWith("Intent has expired");
    });

    it("Should reject intent with invalid nonce", async function () {
      const { intentEngine, user1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      const intent = createValidIntent(user1, inputToken, outputToken, 5); // Wrong nonce
      const signature = await signIntent(intent, user1, intentEngine.target);

      const signedIntent = { intent, signature };

      await expect(intentEngine.connect(user1).createIntent(signedIntent))
        .to.be.revertedWith("Invalid nonce");
    });

    it("Should reject intent with unsupported chain", async function () {
      const { intentEngine, user1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      const intent = createValidIntent(user1, inputToken, outputToken);
      intent.sourceChain = 999; // Unsupported chain

      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      await expect(intentEngine.connect(user1).createIntent(signedIntent))
        .to.be.revertedWith("Source chain not supported");
    });
  });

  describe("Intent Fulfillment", function () {
    it("Should fulfill a valid intent", async function () {
      const { intentEngine, user1, solver1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create intent
      const intent = createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      await intentEngine.connect(user1).createIntent(signedIntent);
      const intentHash = await intentEngine.computeIntentHash(intent);

      // Fulfill intent
      const fulfillment = {
        intentHash: intentHash,
        solver: solver1.address,
        outputAmount: ethers.parseEther("98"),
        proof: "0x1234"
      };

      await expect(intentEngine.connect(solver1).fulfillIntent(fulfillment))
        .to.emit(intentEngine, "IntentFulfilled")
        .withArgs(intentHash, solver1.address, fulfillment.outputAmount);

      expect(await intentEngine.isIntentFulfilled(intentHash)).to.be.true;
    });

    it("Should reject fulfillment by unauthorized solver", async function () {
      const { intentEngine, user1, user2, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create intent
      const intent = createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      await intentEngine.connect(user1).createIntent(signedIntent);
      const intentHash = await intentEngine.computeIntentHash(intent);

      // Try to fulfill with unauthorized solver
      const fulfillment = {
        intentHash: intentHash,
        solver: user2.address,
        outputAmount: ethers.parseEther("98"),
        proof: "0x1234"
      };

      await expect(intentEngine.connect(user2).fulfillIntent(fulfillment))
        .to.be.revertedWith("Unauthorized solver");
    });

    it("Should reject fulfillment with insufficient output amount", async function () {
      const { intentEngine, user1, solver1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create intent
      const intent = createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      await intentEngine.connect(user1).createIntent(signedIntent);
      const intentHash = await intentEngine.computeIntentHash(intent);

      // Try to fulfill with insufficient amount
      const fulfillment = {
        intentHash: intentHash,
        solver: solver1.address,
        outputAmount: ethers.parseEther("90"), // Less than minimum
        proof: "0x1234"
      };

      await expect(intentEngine.connect(solver1).fulfillIntent(fulfillment))
        .to.be.revertedWith("Insufficient output amount");
    });
  });

  describe("Intent Cancellation", function () {
    it("Should allow user to cancel their intent", async function () {
      const { intentEngine, user1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create intent
      const intent = createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      await intentEngine.connect(user1).createIntent(signedIntent);
      const intentHash = await intentEngine.computeIntentHash(intent);

      // Cancel intent
      await expect(intentEngine.connect(user1).cancelIntent(intentHash))
        .to.emit(intentEngine, "IntentCancelled")
        .withArgs(intentHash, user1.address);

      expect(await intentEngine.isIntentCancelled(intentHash)).to.be.true;
    });

    it("Should reject cancellation by non-owner", async function () {
      const { intentEngine, user1, user2, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create intent
      const intent = createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      await intentEngine.connect(user1).createIntent(signedIntent);
      const intentHash = await intentEngine.computeIntentHash(intent);

      // Try to cancel with different user
      await expect(intentEngine.connect(user2).cancelIntent(intentHash))
        .to.be.revertedWith("Only user can cancel");
    });
  });

  describe("Batch Operations", function () {
    it("Should return correct batch intent statuses", async function () {
      const { intentEngine, user1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create multiple intents
      const intent1 = createValidIntent(user1, inputToken, outputToken, 0);
      const intent2 = createValidIntent(user1, inputToken, outputToken, 1);

      const signature1 = await signIntent(intent1, user1, intentEngine.target);
      const signature2 = await signIntent(intent2, user1, intentEngine.target);

      await intentEngine.connect(user1).createIntent({ intent: intent1, signature: signature1 });
      await intentEngine.connect(user1).createIntent({ intent: intent2, signature: signature2 });

      const hash1 = await intentEngine.computeIntentHash(intent1);
      const hash2 = await intentEngine.computeIntentHash(intent2);

      // Get batch statuses
      const statuses = await intentEngine.getIntentStatuses([hash1, hash2]);

      expect(statuses.length).to.equal(2);
      expect(statuses[0].exists).to.be.true;
      expect(statuses[0].fulfilled).to.be.false;
      expect(statuses[1].exists).to.be.true;
      expect(statuses[1].fulfilled).to.be.false;
    });
  });

  describe("Access Control", function () {
    it("Should allow owner to authorize solvers", async function () {
      const { intentEngine, owner, user1 } = await loadFixture(deployIntentEngineFixture);

      await expect(intentEngine.connect(owner).setSolverAuthorization(user1.address, true))
        .to.emit(intentEngine, "SolverAuthorized")
        .withArgs(user1.address, true);

      expect(await intentEngine.authorizedSolvers(user1.address)).to.be.true;
    });

    it("Should reject solver authorization by non-owner", async function () {
      const { intentEngine, user1, user2 } = await loadFixture(deployIntentEngineFixture);

      await expect(intentEngine.connect(user1).setSolverAuthorization(user2.address, true))
        .to.be.revertedWithCustomError(intentEngine, "OwnableUnauthorizedAccount");
    });

    it("Should allow owner to pause and unpause", async function () {
      const { intentEngine, owner } = await loadFixture(deployIntentEngineFixture);

      await intentEngine.connect(owner).pause();
      expect(await intentEngine.paused()).to.be.true;

      await intentEngine.connect(owner).unpause();
      expect(await intentEngine.paused()).to.be.false;
    });
  });
});