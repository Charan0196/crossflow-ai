import { expect } from "chai";
import hre from "hardhat";
const { ethers } = hre;

describe("TestContract", function () {
  let testContract;
  let owner;

  beforeEach(async function () {
    [owner] = await ethers.getSigners();
    
    const TestContract = await ethers.getContractFactory("TestContract");
    testContract = await TestContract.deploy("Hello CrossFlow AI!");
    await testContract.waitForDeployment();
  });

  it("Should set the initial message", async function () {
    expect(await testContract.getMessage()).to.equal("Hello CrossFlow AI!");
  });

  it("Should update the message", async function () {
    await testContract.setMessage("Phase 1 Infrastructure Ready!");
    expect(await testContract.getMessage()).to.equal("Phase 1 Infrastructure Ready!");
  });
});