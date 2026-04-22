import { expect } from "chai";
import hre from "hardhat";
const { ethers } = hre;

describe("IntentLib", function () {
  let intentLibTest;
  let owner, user1, user2;

  // Deploy a test contract that uses IntentLib
  before(async function () {
    [owner, user1, user2] = await ethers.getSigners();

    // Create a test contract that exposes IntentLib functions
    const IntentLibTest = await ethers.getContractFactory("IntentLibTest");
    intentLibTest = await IntentLibTest.deploy();
  });

  describe("Hash Computation", function () {
    it("Should compute consistent intent hashes", async function () {
      const intent = {
        user: user1.address,
        sourceChain: 1,
        destinationChain: 137,
        inputToken: ethers.ZeroAddress,
        outputToken: ethers.ZeroAddress,
        inputAmount: ethers.parseEther("100"),
        minimumOutputAmount: ethers.parseEther("95"),
        deadline: Math.floor(Date.now() / 1000) + 3600,
        nonce: 0,
        recipient: user1.address
      };

      const hash1 = await intentLibTest.computeIntentHash(intent);
      const hash2 = await intentLibTest.computeIntentHash(intent);

      expect(hash1).to.equal(hash2);
      expect(hash1).to.not.equal(ethers.ZeroHash);
    });

    it("Should produce different hashes for different intents", async function () {
      const intent1 = {
        user: user1.address,
        sourceChain: 1,
        destinationChain: 137,
        inputToken: ethers.ZeroAddress,
        outputToken: ethers.ZeroAddress,
        inputAmount: ethers.parseEther("100"),
        minimumOutputAmount: ethers.parseEther("95"),
        deadline: Math.floor(Date.now() / 1000) + 3600,
        nonce: 0,
        recipient: user1.address
      };

      const intent2 = { ...intent1, nonce: 1 };

      const hash1 = await intentLibTest.computeIntentHash(intent1);
      const hash2 = await intentLibTest.computeIntentHash(intent2);

      expect(hash1).to.not.equal(hash2);
    });
  });

  describe("Domain Separator", function () {
    it("Should compute correct domain separator", async function () {
      const name = "Test Contract";
      const version = "1.0.0";
      const chainId = await ethers.provider.getNetwork().then(n => n.chainId);
      const verifyingContract = intentLibTest.target;

      const domainSeparator = await intentLibTest.computeDomainSeparator(
        name,
        version,
        chainId,
        verifyingContract
      );

      expect(domainSeparator).to.not.equal(ethers.ZeroHash);
    });
  });

  describe("Intent Validation", function () {
    it("Should validate correct intent", async function () {
      const intent = {
        user: user1.address,
        sourceChain: 1,
        destinationChain: 137,
        inputToken: user1.address, // Non-zero address
        outputToken: user2.address, // Non-zero address
        inputAmount: ethers.parseEther("100"),
        minimumOutputAmount: ethers.parseEther("95"),
        deadline: Math.floor(Date.now() / 1000) + 3600,
        nonce: 0,
        recipient: user1.address
      };

      const [valid, reason] = await intentLibTest.validateIntent(intent);
      expect(valid).to.be.true;
      expect(reason).to.equal("");
    });

    it("Should reject intent with expired deadline", async function () {
      const intent = {
        user: user1.address,
        sourceChain: 1,
        destinationChain: 137,
        inputToken: user1.address,
        outputToken: user2.address,
        inputAmount: ethers.parseEther("100"),
        minimumOutputAmount: ethers.parseEther("95"),
        deadline: Math.floor(Date.now() / 1000) - 3600, // Expired
        nonce: 0,
        recipient: user1.address
      };

      const [valid, reason] = await intentLibTest.validateIntent(intent);
      expect(valid).to.be.false;
      expect(reason).to.equal("Intent has expired");
    });

    it("Should reject intent with zero amounts", async function () {
      const intent = {
        user: user1.address,
        sourceChain: 1,
        destinationChain: 137,
        inputToken: user1.address,
        outputToken: user2.address,
        inputAmount: 0, // Invalid
        minimumOutputAmount: ethers.parseEther("95"),
        deadline: Math.floor(Date.now() / 1000) + 3600,
        nonce: 0,
        recipient: user1.address
      };

      const [valid, reason] = await intentLibTest.validateIntent(intent);
      expect(valid).to.be.false;
      expect(reason).to.equal("Input amount must be greater than zero");
    });
  });

  describe("Signature Recovery", function () {
    it("Should recover correct signer", async function () {
      const intent = {
        user: user1.address,
        sourceChain: 1,
        destinationChain: 137,
        inputToken: user1.address,
        outputToken: user2.address,
        inputAmount: ethers.parseEther("100"),
        minimumOutputAmount: ethers.parseEther("95"),
        deadline: Math.floor(Date.now() / 1000) + 3600,
        nonce: 0,
        recipient: user1.address
      };

      const domain = {
        name: "Test Contract",
        version: "1.0.0",
        chainId: await ethers.provider.getNetwork().then(n => n.chainId),
        verifyingContract: intentLibTest.target
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

      const signature = await user1.signTypedData(domain, types, intent);
      const domainSeparator = await intentLibTest.computeDomainSeparator(
        domain.name,
        domain.version,
        domain.chainId,
        domain.verifyingContract
      );

      const signedIntent = { intent, signature };
      const recoveredSigner = await intentLibTest.recoverSigner(signedIntent, domainSeparator);

      expect(recoveredSigner).to.equal(user1.address);
    });
  });

  describe("Gas Estimation", function () {
    it("Should provide reasonable gas estimates", async function () {
      const intent = {
        user: user1.address,
        sourceChain: 1,
        destinationChain: 137, // Cross-chain
        inputToken: user1.address,
        outputToken: user2.address,
        inputAmount: ethers.parseEther("100"),
        minimumOutputAmount: ethers.parseEther("95"),
        deadline: Math.floor(Date.now() / 1000) + 3600,
        nonce: 0,
        recipient: user1.address
      };

      const gasEstimate = await intentLibTest.estimateGasCost(intent);
      expect(gasEstimate).to.be.greaterThan(0);
      expect(gasEstimate).to.be.lessThan(ethers.parseUnits("1", "gwei")); // Reasonable upper bound
    });

    it("Should estimate higher gas for cross-chain operations", async function () {
      const sameChainIntent = {
        user: user1.address,
        sourceChain: 1,
        destinationChain: 1, // Same chain
        inputToken: user1.address,
        outputToken: user2.address,
        inputAmount: ethers.parseEther("100"),
        minimumOutputAmount: ethers.parseEther("95"),
        deadline: Math.floor(Date.now() / 1000) + 3600,
        nonce: 0,
        recipient: user1.address
      };

      const crossChainIntent = { ...sameChainIntent, destinationChain: 137 };

      const sameChainGas = await intentLibTest.estimateGasCost(sameChainIntent);
      const crossChainGas = await intentLibTest.estimateGasCost(crossChainIntent);

      expect(crossChainGas).to.be.greaterThan(sameChainGas);
    });
  });
});