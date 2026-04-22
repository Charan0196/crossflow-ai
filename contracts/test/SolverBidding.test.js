import { expect } from "chai";
import hre from "hardhat";
const { ethers } = hre;
import { time, loadFixture } from "@nomicfoundation/hardhat-network-helpers";

describe("Solver Bidding System", function () {
  // Test fixture for deploying contracts
  async function deployIntentEngineFixture() {
    const [owner, user1, solver1, solver2, solver3] = await ethers.getSigners();

    const IntentEngine = await ethers.getContractFactory("IntentEngine");
    const intentEngine = await IntentEngine.deploy(owner.address);

    // Authorize solvers
    await intentEngine.setSolverAuthorization(solver1.address, true);
    await intentEngine.setSolverAuthorization(solver2.address, true);
    await intentEngine.setSolverAuthorization(solver3.address, true);

    // Mock ERC20 tokens for testing
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    const inputToken = await MockERC20.deploy("Input Token", "INPUT", 18);
    const outputToken = await MockERC20.deploy("Output Token", "OUTPUT", 18);

    // Set up supported tokens on all supported chains
    const supportedChains = [1, 137, 42161, 10, 56, 8453];
    
    for (const chainId of supportedChains) {
      await intentEngine.setSupportedToken(inputToken.target, chainId, true);
      await intentEngine.setSupportedToken(outputToken.target, chainId, true);
    }

    return {
      intentEngine,
      owner,
      user1,
      solver1,
      solver2,
      solver3,
      inputToken,
      outputToken
    };
  }

  // Helper function to create a valid intent
  async function createValidIntent(user, inputToken, outputToken, nonce = 0) {
    const currentTime = await time.latest();
    const deadline = currentTime + 3600; // 1 hour from now
    
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

  describe("Solver Bidding", function () {
    it("Should allow authorized solvers to submit bids", async function () {
      const { intentEngine, user1, solver1, solver2, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create and submit intent
      const intent = await createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      const tx = await intentEngine.connect(user1).createIntent(signedIntent);
      const receipt = await tx.wait();
      
      // Get intent hash from event
      const intentCreatedEvent = receipt.logs.find(log => 
        log.fragment && log.fragment.name === "IntentCreated"
      );
      const intentHash = intentCreatedEvent.args[0];

      // Solver 1 submits bid
      await expect(
        intentEngine.connect(solver1).submitSolverBid(
          intentHash,
          ethers.parseEther("96"), // Output amount
          300, // 5 minutes execution time
          ethers.parseEther("0.01"), // Gas fee estimate
          ethers.parseEther("0.005") // Solver fee
        )
      ).to.emit(intentEngine, "SolverBidReceived")
       .withArgs(intentHash, solver1.address, ethers.parseEther("96"));

      // Solver 2 submits better bid
      await expect(
        intentEngine.connect(solver2).submitSolverBid(
          intentHash,
          ethers.parseEther("97"), // Better output amount
          240, // Faster execution time
          ethers.parseEther("0.008"), // Lower gas fee
          ethers.parseEther("0.004") // Lower solver fee
        )
      ).to.emit(intentEngine, "SolverBidReceived")
       .withArgs(intentHash, solver2.address, ethers.parseEther("97"));

      // Check bids were recorded
      const bid1 = await intentEngine.getSolverBid(intentHash, solver1.address);
      expect(bid1.solver).to.equal(solver1.address);
      expect(bid1.outputAmount).to.equal(ethers.parseEther("96"));
      expect(bid1.isValid).to.be.true;

      const bid2 = await intentEngine.getSolverBid(intentHash, solver2.address);
      expect(bid2.solver).to.equal(solver2.address);
      expect(bid2.outputAmount).to.equal(ethers.parseEther("97"));
      expect(bid2.isValid).to.be.true;

      // Check bidders list
      const bidders = await intentEngine.getIntentBidders(intentHash);
      expect(bidders).to.have.lengthOf(2);
      expect(bidders).to.include(solver1.address);
      expect(bidders).to.include(solver2.address);
    });

    it("Should reject bids from unauthorized solvers", async function () {
      const { intentEngine, user1, solver1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create unauthorized solver
      const [, , , , , unauthorizedSolver] = await ethers.getSigners();

      // Create and submit intent
      const intent = await createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      const tx = await intentEngine.connect(user1).createIntent(signedIntent);
      const receipt = await tx.wait();
      
      const intentCreatedEvent = receipt.logs.find(log => 
        log.fragment && log.fragment.name === "IntentCreated"
      );
      const intentHash = intentCreatedEvent.args[0];

      // Unauthorized solver tries to bid
      await expect(
        intentEngine.connect(unauthorizedSolver).submitSolverBid(
          intentHash,
          ethers.parseEther("96"),
          300,
          ethers.parseEther("0.01"),
          ethers.parseEther("0.005")
        )
      ).to.be.revertedWith("Unauthorized solver");
    });

    it("Should reject bids with insufficient output amount", async function () {
      const { intentEngine, user1, solver1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create and submit intent
      const intent = await createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      const tx = await intentEngine.connect(user1).createIntent(signedIntent);
      const receipt = await tx.wait();
      
      const intentCreatedEvent = receipt.logs.find(log => 
        log.fragment && log.fragment.name === "IntentCreated"
      );
      const intentHash = intentCreatedEvent.args[0];

      // Solver tries to bid with insufficient output amount
      await expect(
        intentEngine.connect(solver1).submitSolverBid(
          intentHash,
          ethers.parseEther("90"), // Less than minimum output (95)
          300,
          ethers.parseEther("0.01"),
          ethers.parseEther("0.005")
        )
      ).to.be.revertedWith("Output amount too low");
    });

    it("Should select best solver based on output amount", async function () {
      const { intentEngine, user1, solver1, solver2, solver3, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create and submit intent
      const intent = await createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      const tx = await intentEngine.connect(user1).createIntent(signedIntent);
      const receipt = await tx.wait();
      
      const intentCreatedEvent = receipt.logs.find(log => 
        log.fragment && log.fragment.name === "IntentCreated"
      );
      const intentHash = intentCreatedEvent.args[0];

      // Multiple solvers submit bids
      await intentEngine.connect(solver1).submitSolverBid(
        intentHash,
        ethers.parseEther("96"),
        300,
        ethers.parseEther("0.01"),
        ethers.parseEther("0.005")
      );

      await intentEngine.connect(solver2).submitSolverBid(
        intentHash,
        ethers.parseEther("98"), // Best output amount
        240,
        ethers.parseEther("0.008"),
        ethers.parseEther("0.004")
      );

      await intentEngine.connect(solver3).submitSolverBid(
        intentHash,
        ethers.parseEther("97"),
        180,
        ethers.parseEther("0.009"),
        ethers.parseEther("0.003")
      );

      // Select best solver
      await expect(
        intentEngine.selectBestSolver(intentHash)
      ).to.emit(intentEngine, "SolverSelected")
       .withArgs(intentHash, solver2.address, ethers.parseEther("98"));

      // Check selected solver
      const selectedSolver = await intentEngine.getSelectedSolver(intentHash);
      expect(selectedSolver).to.equal(solver2.address);
    });

    it("Should prevent duplicate bids from same solver", async function () {
      const { intentEngine, user1, solver1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create and submit intent
      const intent = await createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      const tx = await intentEngine.connect(user1).createIntent(signedIntent);
      const receipt = await tx.wait();
      
      const intentCreatedEvent = receipt.logs.find(log => 
        log.fragment && log.fragment.name === "IntentCreated"
      );
      const intentHash = intentCreatedEvent.args[0];

      // Solver submits first bid
      await intentEngine.connect(solver1).submitSolverBid(
        intentHash,
        ethers.parseEther("96"),
        300,
        ethers.parseEther("0.01"),
        ethers.parseEther("0.005")
      );

      // Solver tries to submit second bid
      await expect(
        intentEngine.connect(solver1).submitSolverBid(
          intentHash,
          ethers.parseEther("97"),
          240,
          ethers.parseEther("0.008"),
          ethers.parseEther("0.004")
        )
      ).to.be.revertedWith("Solver already bid");
    });

    it("Should emit IntentBroadcasted event on intent creation", async function () {
      const { intentEngine, user1, inputToken, outputToken } = await loadFixture(deployIntentEngineFixture);

      // Create and submit intent
      const intent = await createValidIntent(user1, inputToken, outputToken);
      const signature = await signIntent(intent, user1, intentEngine.target);
      const signedIntent = { intent, signature };

      // Check that IntentBroadcasted event is emitted
      await expect(
        intentEngine.connect(user1).createIntent(signedIntent)
      ).to.emit(intentEngine, "IntentBroadcasted");
    });
  });
});