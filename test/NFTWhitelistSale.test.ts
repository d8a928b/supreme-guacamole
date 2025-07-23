import { ethers } from "hardhat";
import { expect } from "chai";
import { NFTWhitelistSale } from "../typechain-types";

describe("NFTWhitelistSale", () => {
  let nft: NFTWhitelistSale;
  let owner: any, user1: any, user2: any;

  beforeEach(async () => {
    [owner, user1, user2] = await ethers.getSigners();
    const NFT = await ethers.getContractFactory("NFTWhitelistSale");
    nft = await NFT.deploy();
    await nft.deployed();
  });

  it("Owner can whitelist addresses", async () => {
    await nft.addToWhitelist([user1.address]);
    expect(await nft.whitelist(user1.address)).to.be.true;
  });

  it("Non-whitelisted address cannot mint", async () => {
    await expect(nft.connect(user1).mint(1, { value: ethers.utils.parseEther("0.003") })).to.be.revertedWith(
      "Not whitelisted"
    );
  });

  it("Whitelisted address can mint within limits", async () => {
    await nft.addToWhitelist([user1.address]);
    await nft.connect(user1).mint(2, { value: ethers.utils.parseEther("0.006") });
    expect(await nft.balanceOf(user1.address)).to.equal(2);
  });

  it("Cannot mint more than 5 per wallet", async () => {
    await nft.addToWhitelist([user1.address]);
    await nft.connect(user1).mint(5, { value: ethers.utils.parseEther("0.015") });
    await expect(nft.connect(user1).mint(1, { value: ethers.utils.parseEther("0.003") })).to.be.revertedWith(
      "Exceeds wallet limit"
    );
  });

  it("Admin cannot mint unless whitelisted", async () => {
    await expect(nft.connect(owner).mint(1, { value: ethers.utils.parseEther("0.003") })).to.be.revertedWith(
      "Not whitelisted"
    );
  });

  it("Owner can withdraw funds", async () => {
    await nft.addToWhitelist([user1.address]);
    await nft.connect(user1).mint(1, { value: ethers.utils.parseEther("0.003") });

    const initialBalance = await ethers.provider.getBalance(owner.address);
    const tx = await nft.withdraw();
    const receipt = await tx.wait();
    const gas = receipt.gasUsed.mul(receipt.effectiveGasPrice);
    const finalBalance = await ethers.provider.getBalance(owner.address);

    expect(finalBalance).to.be.closeTo(
      initialBalance.add(ethers.utils.parseEther("0.003")).sub(gas),
      ethers.utils.parseEther("0.001")
    );
  });
});
