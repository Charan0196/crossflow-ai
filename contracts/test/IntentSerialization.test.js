import { expect } from "chai";
import hre from "hardhat";
const { ethers } = hre;

describe("IntentSerialization", function () {
  let serializationTest;
  let owner, user1, user2;

  before(async function () {
    [owner, user1, user2] = await ethers.getSigners();

    const SerializationTest = await ethers.getContractFactory("IntentSerializationTest");
    serializationTest = await SerializationTest.deploy();
  });

  function createTestIntent() {
    return {
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
  }

  describe("Intent Serialization", function () {
    it("Should serialize and deserialize intent correctly", async function () {
      const originalIntent = createTestIntent();

      const serialized = await serializationTest.serializeIntent(originalIntent);
      const deserialized = await serializationTest.deserializeIntent(serialized);

      expect(deserialized.user).to.equal(originalIntent.user);
      expect(deserialized.sourceChain).to.equal(originalIntent.sourceChain);
      expect(deserialized.destinationChain).to.equal(originalIntent.destinationChain);
      expect(deserialized.inputToken).to.equal(originalIntent.inputToken);
      expect(deserialized.outputToken).to.equal(originalIntent.outputToken);
      expect(deserialized.inputAmount).to.equal(originalIntent.inputAmount);
      expect(deserialized.minimumOutputAmount).to.equal(originalIntent.minimumOutputAmount);
      expect(deserialized.deadline).to.equal(originalIntent.deadline);
      expect(deserialized.nonce).to.equal(originalIntent.nonce);
      expect(deserialized.recipient).to.equal(originalIntent.recipient);
    });

    it("Should produce consistent serialization", async function () {
      const intent = createTestIntent();

      const serialized1 = await serializationTest.serializeIntent(intent);
      const serialized2 = await serializationTest.serializeIntent(intent);

      expect(serialized1).to.equal(serialized2);
    });

    it("Should validate serialized data", async function () {
      const intent = createTestIntent();
      const serialized = await serializationTest.serializeIntent(intent);

      const isValid = await serializationTest.validateSerializedIntent(serialized);
      expect(isValid).to.be.true;

      // Test with invalid data (too short)
      const invalidData = "0x1234";
      const isInvalid = await serializationTest.validateSerializedIntent(invalidData);
      expect(isInvalid).to.be.false;
    });
  });

  describe("SignedIntent Serialization", function () {
    it("Should serialize and deserialize signed intent correctly", async function () {
      const intent = createTestIntent();
      const signature = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef1b";
      
      const signedIntent = { intent, signature };

      const serialized = await serializationTest.serializeSignedIntent(signedIntent);
      const deserialized = await serializationTest.deserializeSignedIntent(serialized);

      expect(deserialized.intent.user).to.equal(intent.user);
      expect(deserialized.signature).to.equal(signature);
    });
  });

  describe("Fulfillment Serialization", function () {
    it("Should serialize and deserialize fulfillment correctly", async function () {
      const fulfillment = {
        intentHash: ethers.keccak256(ethers.toUtf8Bytes("test")),
        solver: user1.address,
        outputAmount: ethers.parseEther("98"),
        proof: "0x1234"
      };

      const serialized = await serializationTest.serializeFulfillment(fulfillment);
      const deserialized = await serializationTest.deserializeFulfillment(serialized);

      expect(deserialized.intentHash).to.equal(fulfillment.intentHash);
      expect(deserialized.solver).to.equal(fulfillment.solver);
      expect(deserialized.outputAmount).to.equal(fulfillment.outputAmount);
      expect(deserialized.proof).to.equal(fulfillment.proof);
    });
  });

  describe("Compression and Utilities", function () {
    it("Should create consistent compressed representation", async function () {
      const intent = createTestIntent();

      const compressed1 = await serializationTest.compressIntent(intent);
      const compressed2 = await serializationTest.compressIntent(intent);

      expect(compressed1).to.equal(compressed2);
      expect(compressed1).to.not.equal(ethers.ZeroHash);
    });

    it("Should create different compressed representations for different intents", async function () {
      const intent1 = createTestIntent();
      const intent2 = { ...intent1, nonce: 1 };

      const compressed1 = await serializationTest.compressIntent(intent1);
      const compressed2 = await serializationTest.compressIntent(intent2);

      expect(compressed1).to.not.equal(compressed2);
    });

    it("Should estimate serialization gas correctly", async function () {
      const intent = createTestIntent();

      const gasEstimate = await serializationTest.estimateSerializationGas(intent);
      expect(gasEstimate).to.be.greaterThan(0);
      expect(gasEstimate).to.be.lessThan(50000); // Reasonable upper bound
    });

    it("Should create merkle leaf", async function () {
      const intent = createTestIntent();

      const leaf = await serializationTest.createMerkleLeaf(intent);
      expect(leaf).to.not.equal(ethers.ZeroHash);
    });
  });

  describe("Batch Operations", function () {
    it("Should batch serialize and deserialize multiple intents", async function () {
      const intents = [
        createTestIntent(),
        { ...createTestIntent(), nonce: 1 },
        { ...createTestIntent(), nonce: 2 }
      ];

      const serialized = await serializationTest.batchSerializeIntents(intents);
      const deserialized = await serializationTest.batchDeserializeIntents(serialized);

      expect(deserialized.length).to.equal(intents.length);
      
      for (let i = 0; i < intents.length; i++) {
        expect(deserialized[i].user).to.equal(intents[i].user);
        expect(deserialized[i].nonce).to.equal(intents[i].nonce);
      }
    });
  });
});