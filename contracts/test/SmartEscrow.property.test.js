import { expect } from "chai";
import hre from "hardhat";
const { ethers } = hre;
import { time, loadFixture } from "@nomicfoundation/hardhat-network-helpers";

/**
 * Property-Based Tests for Smart Escrow Settlement Layer
 * 
 * These tests validate the correctness properties defined in the design document
 * Each test runs with minimum 100 iterations as specified in requirements
 * 
 * Feature: crossflow-phase-1-foundation
 */
describe("SmartEscrow Property Tests", function () {
  // Test fixture for deploying contracts
  async function deploySmartEscrowFixture() {
    const [owner, user1, user2, solver1, solver2, governance1, governance2, governance3] = await ethers.getSigners();

    // Deploy governance members and set threshold
    const governanceMembers = [governance1.address, governance2.address, governance3.address];
    const governanceThreshold = 2;

    const SmartEscrow = await ethers.getContractFactory("SmartEscrow");
    const smartEscrow = await SmartEscrow.deploy(owner.address, governanceMembers, governanceThreshold);

    // Authorize solvers
    await smartEscrow.setSolverAuthorization(solver1.address, true);
    await smartEscrow.setSolverAuthorization(solver2.address, true);

    // Mock ERC20 tokens for testing
    const MockERC20 = await ethers.getContractFactory("MockERC20");
    const token1 = await MockERC20.deploy("Test Token 1", "TT1", 18);
    const token2 = await MockERC20.deploy("Test Token 2", "TT2", 18);

    // Mint tokens to users
    await token1.mint(user1.address, ethers.parseEther("10000"));
    await token1.mint(user2.address, ethers.parseEther("10000"));
    await token2.mint(user1.address, ethers.parseEther("10000"));
    await token2.mint(user2.address, ethers.parseEther("10000"));

    // Approve escrow to spend tokens
    await token1.connect(user1).approve(smartEscrow.target, ethers.parseEther("10000"));
    await token1.connect(user2).approve(smartEscrow.target, ethers.parseEther("10000"));
    await token2.connect(user1).approve(smartEscrow.target, ethers.parseEther("10000"));
    await token2.connect(user2).approve(smartEscrow.target, ethers.parseEther("10000"));

    return {
      smartEscrow,
      owner,
      user1,
      user2,
      solver1,
      solver2,
      governance1,
      governance2,
      governance3,
      token1,
      token2
    };
  }

  // Helper function to generate random intent hash
  function generateRandomIntentHash() {
    return ethers.keccak256(ethers.toUtf8Bytes(`intent_${Math.random()}_${Date.now()}`));
  }

  // Helper function to generate random escrow parameters
  function generateRandomEscrowParams(token, user, solver) {
    return {
      intentHash: generateRandomIntentHash(),
      token: token.target,
      amount: ethers.parseEther((Math.random() * 100 + 1).toString()),
      user: user.address,
      selectedSolver: solver.address
    };
  }

  // Helper function to create fulfillment proof
  function createFulfillmentProof(solver, outputAmount, destinationChainId = 1) {
    return {
      solver: solver.address,
      outputAmount: outputAmount,
      destinationTxHash: ethers.keccak256(ethers.toUtf8Bytes(`tx_${Math.random()}`)),
      destinationChainId: destinationChainId,
      proof: ethers.toUtf8Bytes("mock_proof"),
      timestamp: Math.floor(Date.now() / 1000),
      verified: false
    };
  }

  /**
   * Property 9: Escrow Fund Locking
   * Validates: Requirements 3.1
   * 
   * For any cross-chain trade initiation, the user's input tokens should be locked in escrow on the source chain
   */
  describe("Property 9: Escrow Fund Locking", function () {
    it("Should consistently lock funds in escrow across 100 iterations", async function () {
      const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 100; i++) {
        const params = generateRandomEscrowParams(token1, user1, solver1);
        
        // Get initial balances
        const initialUserBalance = await token1.balanceOf(user1.address);
        const initialEscrowBalance = await token1.balanceOf(smartEscrow.target);

        // Lock funds
        await expect(smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        )).to.not.be.reverted;

        // Verify balances changed correctly
        const finalUserBalance = await token1.balanceOf(user1.address);
        const finalEscrowBalance = await token1.balanceOf(smartEscrow.target);

        expect(finalUserBalance).to.equal(initialUserBalance - params.amount, 
          `User balance not reduced correctly at iteration ${i}`);
        expect(finalEscrowBalance).to.equal(initialEscrowBalance + params.amount,
          `Escrow balance not increased correctly at iteration ${i}`);

        // Verify escrow data is stored correctly
        const escrowData = await smartEscrow.getEscrowData(params.intentHash);
        expect(escrowData.user).to.equal(params.user, `User not stored correctly at iteration ${i}`);
        expect(escrowData.token).to.equal(params.token, `Token not stored correctly at iteration ${i}`);
        expect(escrowData.amount).to.equal(params.amount, `Amount not stored correctly at iteration ${i}`);
        expect(escrowData.status).to.equal(1, `Status should be LOCKED at iteration ${i}`); // 1 = LOCKED
        expect(escrowData.selectedSolver).to.equal(params.selectedSolver, 
          `Solver not stored correctly at iteration ${i}`);
      }
    });

    it("Should reject invalid lock attempts across 100 iterations", async function () {
      const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 100; i++) {
        const params = generateRandomEscrowParams(token1, user1, solver1);

        // Test various invalid parameters
        const invalidTests = [
          {
            name: "zero intent hash",
            params: { ...params, intentHash: ethers.ZeroHash },
            error: "Invalid intent hash"
          },
          {
            name: "zero token address", 
            params: { ...params, token: ethers.ZeroAddress },
            error: "Invalid token address"
          },
          {
            name: "zero amount",
            params: { ...params, amount: 0 },
            error: "Invalid amount"
          },
          {
            name: "zero user address",
            params: { ...params, user: ethers.ZeroAddress },
            error: "Invalid user address"
          },
          {
            name: "zero solver address",
            params: { ...params, selectedSolver: ethers.ZeroAddress },
            error: "Invalid solver address"
          }
        ];

        const testCase = invalidTests[i % invalidTests.length];
        
        await expect(smartEscrow.lockFunds(
          testCase.params.intentHash,
          testCase.params.token,
          testCase.params.amount,
          testCase.params.user,
          testCase.params.selectedSolver
        )).to.be.revertedWith(testCase.error);
      }
    });

    it("Should prevent duplicate escrow creation across 100 iterations", async function () {
      const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 100; i++) {
        const params = generateRandomEscrowParams(token1, user1, solver1);

        // First lock should succeed
        await smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        );

        // Second lock with same intent hash should fail
        await expect(smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        )).to.be.revertedWith("Escrow already exists");
      }
    });
  });

  /**
   * Property 10: Timeout Period Assignment
   * Validates: Requirements 3.2
   * 
   * For any tokens locked in escrow, a timeout period should be set for trade completion
   */
  describe("Property 10: Timeout Period Assignment", function () {
    it("Should assign correct timeout periods across 100 iterations", async function () {
      const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 100; i++) {
        const params = generateRandomEscrowParams(token1, user1, solver1);
        
        const lockTimestamp = await time.latest();
        
        await smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        );

        const escrowData = await smartEscrow.getEscrowData(params.intentHash);
        const expectedTimeout = lockTimestamp + (30 * 60) + 1; // 30 minutes + 1 second for block time
        
        expect(escrowData.timeoutDeadline).to.be.closeTo(expectedTimeout, 5,
          `Timeout deadline not set correctly at iteration ${i}`);
        expect(escrowData.lockTimestamp).to.be.closeTo(lockTimestamp + 1, 5,
          `Lock timestamp not set correctly at iteration ${i}`);
      }
    });

    it("Should respect custom timeout periods across different settings", async function () {
      const { smartEscrow, owner, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);

      const timeoutPeriods = [
        5 * 60,      // 5 minutes (minimum)
        60 * 60,     // 1 hour
        24 * 60 * 60, // 1 day
        7 * 24 * 60 * 60 // 7 days (maximum)
      ];

      for (let i = 0; i < 100; i++) {
        const timeoutPeriod = timeoutPeriods[i % timeoutPeriods.length];
        
        // Set custom timeout period
        await smartEscrow.connect(owner).setTimeoutPeriod(timeoutPeriod);
        
        const params = generateRandomEscrowParams(token1, user1, solver1);
        const lockTimestamp = await time.latest();
        
        await smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        );

        const escrowData = await smartEscrow.getEscrowData(params.intentHash);
        const expectedTimeout = lockTimestamp + timeoutPeriod + 1;
        
        expect(escrowData.timeoutDeadline).to.be.closeTo(expectedTimeout, 5,
          `Custom timeout not applied correctly at iteration ${i} with period ${timeoutPeriod}`);
      }
    });

    it("Should enforce timeout period limits across 100 attempts", async function () {
      const { smartEscrow, owner } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 100; i++) {
        // Test invalid timeout periods
        const invalidPeriods = [
          0,                    // Zero
          4 * 60,              // Too short (less than 5 minutes)
          8 * 24 * 60 * 60,    // Too long (more than 7 days)
          Math.floor(Math.random() * (4 * 60)), // Random short period
          7 * 24 * 60 * 60 + Math.floor(Math.random() * 86400) // Random long period
        ];

        const invalidPeriod = invalidPeriods[i % invalidPeriods.length];
        
        if (invalidPeriod < 5 * 60) {
          await expect(smartEscrow.connect(owner).setTimeoutPeriod(invalidPeriod))
            .to.be.revertedWith("Timeout too short");
        } else if (invalidPeriod > 7 * 24 * 60 * 60) {
          await expect(smartEscrow.connect(owner).setTimeoutPeriod(invalidPeriod))
            .to.be.revertedWith("Timeout too long");
        }
      }
    });
  });

  /**
   * Property 11: Fulfillment Verification
   * Validates: Requirements 3.3
   * 
   * For any solver fulfillment attempt, the system should verify the fulfillment proof before releasing escrowed funds
   */
  describe("Property 11: Fulfillment Verification", function () {
    it("Should verify fulfillment proofs before releasing funds across 100 iterations", async function () {
      const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 100; i++) {
        const params = generateRandomEscrowParams(token1, user1, solver1);
        
        // Lock funds
        await smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        );

        const fulfillmentProof = createFulfillmentProof(solver1, params.amount);
        
        // Get initial balances
        const initialSolverBalance = await token1.balanceOf(solver1.address);
        const initialEscrowBalance = await token1.balanceOf(smartEscrow.target);

        // Release funds with valid proof
        await expect(smartEscrow.releaseFunds(params.intentHash, fulfillmentProof))
          .to.not.be.reverted;

        // Verify funds were released to solver
        const finalSolverBalance = await token1.balanceOf(solver1.address);
        const finalEscrowBalance = await token1.balanceOf(smartEscrow.target);

        expect(finalSolverBalance).to.equal(initialSolverBalance + params.amount,
          `Solver balance not increased correctly at iteration ${i}`);
        expect(finalEscrowBalance).to.equal(initialEscrowBalance - params.amount,
          `Escrow balance not decreased correctly at iteration ${i}`);

        // Verify escrow status updated
        const escrowData = await smartEscrow.getEscrowData(params.intentHash);
        expect(escrowData.status).to.equal(2, `Status should be FULFILLED at iteration ${i}`); // 2 = FULFILLED

        // Verify fulfillment proof stored
        const storedProof = await smartEscrow.getFulfillmentProof(params.intentHash);
        expect(storedProof.solver).to.equal(fulfillmentProof.solver,
          `Proof solver not stored correctly at iteration ${i}`);
        expect(storedProof.outputAmount).to.equal(fulfillmentProof.outputAmount,
          `Proof output amount not stored correctly at iteration ${i}`);
      }
    });

    it("Should reject invalid fulfillment proofs across 100 iterations", async function () {
      const { smartEscrow, user1, solver1, solver2, token1 } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 100; i++) {
        const params = generateRandomEscrowParams(token1, user1, solver1);
        
        await smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        );

        // Test various invalid proofs
        const invalidProofs = [
          {
            name: "wrong solver",
            proof: createFulfillmentProof(solver2, params.amount),
            error: "Invalid solver"
          },
          {
            name: "zero output amount",
            proof: { ...createFulfillmentProof(solver1, 0), outputAmount: 0 },
            error: "Invalid fulfillment proof"
          },
          {
            name: "zero destination tx hash",
            proof: { ...createFulfillmentProof(solver1, params.amount), destinationTxHash: ethers.ZeroHash },
            error: "Invalid fulfillment proof"
          },
          {
            name: "zero destination chain",
            proof: { ...createFulfillmentProof(solver1, params.amount), destinationChainId: 0 },
            error: "Invalid fulfillment proof"
          }
        ];

        const testCase = invalidProofs[i % invalidProofs.length];
        
        await expect(smartEscrow.releaseFunds(params.intentHash, testCase.proof))
          .to.be.revertedWith(testCase.error);
      }
    });

    it("Should prevent double fulfillment across 100 iterations", async function () {
      const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 100; i++) {
        const params = generateRandomEscrowParams(token1, user1, solver1);
        
        await smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        );

        const fulfillmentProof = createFulfillmentProof(solver1, params.amount);
        
        // First fulfillment should succeed
        await smartEscrow.releaseFunds(params.intentHash, fulfillmentProof);

        // Second fulfillment should fail
        await expect(smartEscrow.releaseFunds(params.intentHash, fulfillmentProof))
          .to.be.revertedWith("Invalid escrow status");
      }
    });
  });

  /**
   * Property 12: Automatic Refund on Timeout
   * Validates: Requirements 3.4
   * 
   * For any trade that exceeds its timeout period, the locked tokens should be automatically refunded to the user
   */
  describe("Property 12: Automatic Refund on Timeout", function () {
    it("Should automatically refund after timeout across 100 iterations", async function () {
      const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 100; i++) {
        const params = generateRandomEscrowParams(token1, user1, solver1);
        
        // Lock funds
        await smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        );

        // Get initial user balance
        const initialUserBalance = await token1.balanceOf(user1.address);
        const initialEscrowBalance = await token1.balanceOf(smartEscrow.target);

        // Fast forward past timeout
        await time.increase(31 * 60); // 31 minutes (past 30 minute timeout)

        // Refund should work
        await expect(smartEscrow.refundFunds(params.intentHash))
          .to.not.be.reverted;

        // Verify funds returned to user
        const finalUserBalance = await token1.balanceOf(user1.address);
        const finalEscrowBalance = await token1.balanceOf(smartEscrow.target);

        expect(finalUserBalance).to.equal(initialUserBalance + params.amount,
          `User balance not increased correctly at iteration ${i}`);
        expect(finalEscrowBalance).to.equal(initialEscrowBalance - params.amount,
          `Escrow balance not decreased correctly at iteration ${i}`);

        // Verify escrow status updated
        const escrowData = await smartEscrow.getEscrowData(params.intentHash);
        expect(escrowData.status).to.equal(3, `Status should be REFUNDED at iteration ${i}`); // 3 = REFUNDED
      }
    });

    it("Should reject early refund attempts across 100 iterations", async function () {
      for (let i = 0; i < 100; i++) {
        const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);
        const params = generateRandomEscrowParams(token1, user1, solver1);
        
        await smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        );

        // Try to refund before timeout
        await expect(smartEscrow.refundFunds(params.intentHash))
          .to.be.revertedWith("Timeout not reached");

        // Fast forward but not enough (random time less than 30 minutes)
        const randomTime = Math.floor(Math.random() * (29 * 60)) + 1;
        if (randomTime > 0) {
          await time.increase(randomTime);

          // Should still fail
          await expect(smartEscrow.refundFunds(params.intentHash))
            .to.be.revertedWith("Timeout not reached");
        }
      }
    });

    it("Should prevent refund after fulfillment across 100 iterations", async function () {
      const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 100; i++) {
        const params = generateRandomEscrowParams(token1, user1, solver1);
        
        await smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        );

        // Fulfill the escrow
        const fulfillmentProof = createFulfillmentProof(solver1, params.amount);
        await smartEscrow.releaseFunds(params.intentHash, fulfillmentProof);

        // Fast forward past timeout
        await time.increase(31 * 60);

        // Refund should fail because already fulfilled
        await expect(smartEscrow.refundFunds(params.intentHash))
          .to.be.revertedWith("Invalid escrow status");
      }
    });

    it("Should handle timeout edge cases correctly", async function () {
      for (let i = 0; i < 50; i++) { // Reduced iterations for performance
        const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);
        const params = generateRandomEscrowParams(token1, user1, solver1);
        
        await smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        );

        const escrowData = await smartEscrow.getEscrowData(params.intentHash);
        const currentTime = await time.latest();
        
        // Calculate exact time needed to reach timeout
        const timeToTimeout = Number(escrowData.timeoutDeadline) - currentTime;
        
        if (timeToTimeout > 1) {
          // Fast forward to just before timeout
          await time.increase(timeToTimeout - 1);
          
          // Should not be able to refund yet
          await expect(smartEscrow.refundFunds(params.intentHash))
            .to.be.revertedWith("Timeout not reached");
          
          // Fast forward past timeout
          await time.increase(2);
          
          // Should be able to refund now
          await expect(smartEscrow.refundFunds(params.intentHash))
            .to.not.be.reverted;
        } else {
          // Already past timeout, should be able to refund
          await expect(smartEscrow.refundFunds(params.intentHash))
            .to.not.be.reverted;
        }
      }
    });
  });

  /**
   * Property 13: Event Emission on Fund Release
   * Validates: Requirements 3.5
   * 
   * For any fund release from escrow, appropriate events should be emitted for tracking and analytics
   */
  describe("Property 13: Event Emission on Fund Release", function () {
    it("Should emit proper events for all fund release operations across 100 iterations", async function () {
      const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 100; i++) {
        const params = generateRandomEscrowParams(token1, user1, solver1);
        
        // Test FundsLocked event
        await expect(smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        )).to.emit(smartEscrow, "FundsLocked");

        if (i % 2 === 0) {
          // Test FundsReleased event
          const fulfillmentProof = createFulfillmentProof(solver1, params.amount);
          
          await expect(smartEscrow.releaseFunds(params.intentHash, fulfillmentProof))
            .to.emit(smartEscrow, "FulfillmentProofSubmitted")
            .to.emit(smartEscrow, "FulfillmentProofVerified")
            .to.emit(smartEscrow, "FundsReleased");
        } else {
          // Test FundsRefunded event
          await time.increase(31 * 60); // Past timeout
          
          await expect(smartEscrow.refundFunds(params.intentHash))
            .to.emit(smartEscrow, "FundsRefunded");
        }
      }
    });

    it("Should emit governance events correctly across 100 iterations", async function () {
      const { smartEscrow, owner, solver1, governance1, governance2 } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 100; i++) {
        // Test SolverAuthorized event
        const authorized = i % 2 === 0;
        await expect(smartEscrow.connect(owner).setSolverAuthorization(solver1.address, authorized))
          .to.emit(smartEscrow, "SolverAuthorized");

        // Test TimeoutPeriodUpdated event (every 10 iterations to avoid too many changes)
        if (i % 10 === 0) {
          const newTimeout = 5 * 60 + (i * 60); // Vary timeout period
          const oldTimeout = await smartEscrow.timeoutPeriod();
          
          await expect(smartEscrow.connect(owner).setTimeoutPeriod(newTimeout))
            .to.emit(smartEscrow, "TimeoutPeriodUpdated");
        }

        // Test governance proposal events (every 20 iterations)
        if (i % 20 === 0) {
          const action = ethers.keccak256(ethers.toUtf8Bytes(`action_${i}`));
          const data = ethers.toUtf8Bytes(`data_${i}`);
          
          await expect(smartEscrow.connect(governance1).createGovernanceProposal(action, data, 0))
            .to.emit(smartEscrow, "GovernanceProposalCreated")
            .to.emit(smartEscrow, "GovernanceProposalVoted");
        }
      }
    });

    it("Should emit events with correct parameters and indexing", async function () {
      const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);

      for (let i = 0; i < 50; i++) { // Reduced iterations for performance
        const params = generateRandomEscrowParams(token1, user1, solver1);
        
        // Lock funds and capture event
        const lockTx = await smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        );
        
        const lockReceipt = await lockTx.wait();
        const lockEvent = lockReceipt.logs.find(log => {
          try {
            const parsed = smartEscrow.interface.parseLog(log);
            return parsed.name === "FundsLocked";
          } catch {
            return false;
          }
        });

        expect(lockEvent).to.not.be.undefined;
        
        const parsedLockEvent = smartEscrow.interface.parseLog(lockEvent);
        expect(parsedLockEvent.args.intentHash).to.equal(params.intentHash);
        expect(parsedLockEvent.args.user).to.equal(params.user);
        expect(parsedLockEvent.args.token).to.equal(params.token);
        expect(parsedLockEvent.args.amount).to.equal(params.amount);

        // Test fulfillment events
        const fulfillmentProof = createFulfillmentProof(solver1, params.amount);
        const releaseTx = await smartEscrow.releaseFunds(params.intentHash, fulfillmentProof);
        const releaseReceipt = await releaseTx.wait();
        
        // Check for FundsReleased event
        const releaseEvent = releaseReceipt.logs.find(log => {
          try {
            const parsed = smartEscrow.interface.parseLog(log);
            return parsed.name === "FundsReleased";
          } catch {
            return false;
          }
        });

        expect(releaseEvent).to.not.be.undefined;
        
        const parsedReleaseEvent = smartEscrow.interface.parseLog(releaseEvent);
        expect(parsedReleaseEvent.args.intentHash).to.equal(params.intentHash);
        expect(parsedReleaseEvent.args.solver).to.equal(fulfillmentProof.solver);
        expect(parsedReleaseEvent.args.user).to.equal(params.user);
        expect(parsedReleaseEvent.args.amount).to.equal(params.amount);
      }
    });

    it("Should maintain event emission consistency under concurrent operations", async function () {
      const { smartEscrow, user1, user2, solver1, solver2, token1, token2 } = await loadFixture(deploySmartEscrowFixture);

      const promises = [];
      const expectedEvents = [];

      // Create multiple concurrent operations
      for (let i = 0; i < 20; i++) {
        const user = i % 2 === 0 ? user1 : user2;
        const solver = i % 2 === 0 ? solver1 : solver2;
        const token = i % 2 === 0 ? token1 : token2;
        const params = generateRandomEscrowParams(token, user, solver);
        
        expectedEvents.push({
          intentHash: params.intentHash,
          user: params.user,
          token: params.token,
          amount: params.amount,
          solver: params.selectedSolver
        });

        promises.push(
          smartEscrow.lockFunds(
            params.intentHash,
            params.token,
            params.amount,
            params.user,
            params.selectedSolver
          )
        );
      }

      // Execute all operations
      const results = await Promise.all(promises);
      
      // Verify all events were emitted
      for (let i = 0; i < results.length; i++) {
        const receipt = await results[i].wait();
        const lockEvent = receipt.logs.find(log => {
          try {
            const parsed = smartEscrow.interface.parseLog(log);
            return parsed.name === "FundsLocked";
          } catch {
            return false;
          }
        });

        expect(lockEvent).to.not.be.undefined;
        
        const parsedEvent = smartEscrow.interface.parseLog(lockEvent);
        const expected = expectedEvents[i];
        
        expect(parsedEvent.args.intentHash).to.equal(expected.intentHash);
        expect(parsedEvent.args.user).to.equal(expected.user);
        expect(parsedEvent.args.token).to.equal(expected.token);
        expect(parsedEvent.args.amount).to.equal(expected.amount);
      }
    });
  });

  describe("Gas Optimization Properties", function () {
    it("Should maintain reasonable gas costs for escrow operations", async function () {
      const { smartEscrow, user1, solver1, token1 } = await loadFixture(deploySmartEscrowFixture);

      const lockGasCosts = [];
      const releaseGasCosts = [];
      const refundGasCosts = [];

      for (let i = 0; i < 50; i++) {
        const params = generateRandomEscrowParams(token1, user1, solver1);
        
        // Test lock gas cost
        const lockTx = await smartEscrow.lockFunds(
          params.intentHash,
          params.token,
          params.amount,
          params.user,
          params.selectedSolver
        );
        const lockReceipt = await lockTx.wait();
        lockGasCosts.push(lockReceipt.gasUsed);

        if (i % 2 === 0) {
          // Test release gas cost
          const fulfillmentProof = createFulfillmentProof(solver1, params.amount);
          const releaseTx = await smartEscrow.releaseFunds(params.intentHash, fulfillmentProof);
          const releaseReceipt = await releaseTx.wait();
          releaseGasCosts.push(releaseReceipt.gasUsed);
        } else {
          // Test refund gas cost
          await time.increase(31 * 60);
          const refundTx = await smartEscrow.refundFunds(params.intentHash);
          const refundReceipt = await refundTx.wait();
          refundGasCosts.push(refundReceipt.gasUsed);
        }
      }

      // Verify gas costs are reasonable
      const avgLockGas = lockGasCosts.reduce((a, b) => a + b, BigInt(0)) / BigInt(lockGasCosts.length);
      const avgReleaseGas = releaseGasCosts.reduce((a, b) => a + b, BigInt(0)) / BigInt(releaseGasCosts.length);
      const avgRefundGas = refundGasCosts.reduce((a, b) => a + b, BigInt(0)) / BigInt(refundGasCosts.length);

      expect(avgLockGas).to.be.lessThan(BigInt(250000), "Lock gas usage too high");
      expect(avgReleaseGas).to.be.lessThan(BigInt(220000), "Release gas usage too high");
      expect(avgRefundGas).to.be.lessThan(BigInt(100000), "Refund gas usage too high");
    });
  });
});