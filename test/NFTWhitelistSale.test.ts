import "@nomicfoundation/hardhat-ethers";
import "@nomicfoundation/hardhat-chai-matchers";
import { ethers } from "hardhat";
import { expect } from "chai";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";
import { NFTWhitelistSale } from "../typechain-types";

describe("NFTWhitelistSale", function () {
  let deployer: SignerWithAddress, addr1: SignerWithAddress, addr2: SignerWithAddress, addr3: SignerWithAddress;

  let nftContract: NFTWhitelistSale;

  const PRICE = ethers.parseEther("0.003");

  beforeEach(async () => {
    [deployer, addr1, addr2, addr3] = await ethers.getSigners();

    const factory = await ethers.getContractFactory("NFTWhitelistSale");
    nftContract = (await factory.connect(deployer).deploy()) as NFTWhitelistSale;
  });

  describe("Deployment", function () {
    it("Should set name and symbol correctly", async () => {
      expect(await nftContract.name()).to.equal("WhitelistNFT");
      expect(await nftContract.symbol()).to.equal("WLNFT");
    });

    it("Should start with zero minted", async () => {
      expect(await nftContract.totalMinted()).to.equal(0n);
    });
  });

  describe("Whitelist Management", function () {
    it("Should allow owner to add and remove from whitelist", async () => {
      await nftContract.addToWhitelist([addr1.address, addr2.address]);
      expect(await nftContract.whitelist(addr1.address)).to.equal(true);
      expect(await nftContract.whitelist(addr2.address)).to.equal(true);

      await nftContract.removeFromWhitelist([addr1.address]);
      expect(await nftContract.whitelist(addr1.address)).to.equal(false);
    });

    it("Should revert if non-owner tries to modify whitelist", async () => {
      await expect(nftContract.connect(addr1).addToWhitelist([addr3.address])).to.be.revertedWithCustomError(
        nftContract,
        "OwnableUnauthorizedAccount"
      );
    });
  });

  describe("Minting", function () {
    beforeEach(async () => {
      await nftContract.addToWhitelist([addr1.address]);
    });

    it("Should mint NFTs correctly for whitelisted users", async () => {
      await nftContract.connect(addr1).mint(2, { value: PRICE * 2n });

      expect(await nftContract.totalMinted()).to.equal(2n);
      expect(await nftContract.balanceOf(addr1.address)).to.equal(2n);
    });

    it("Should fail if not whitelisted", async () => {
      await expect(nftContract.connect(addr2).mint(1, { value: PRICE })).to.be.revertedWith("Not whitelisted");
    });

    it("Should fail if sent incorrect ETH value", async () => {
      await expect(nftContract.connect(addr1).mint(1, { value: PRICE - 1n })).to.be.revertedWith("Incorrect ETH value");
    });

    it("Should fail if minting more than max per wallet", async () => {
      await nftContract.connect(addr1).mint(5, { value: PRICE * 5n });

      await expect(nftContract.connect(addr1).mint(1, { value: PRICE })).to.be.revertedWith("Exceeds wallet limit");
    });

    it("Should fail if minting exceeds max supply", async () => {
      const signers = await ethers.getSigners();
      const whitelistAddresses = signers.slice(1, 11);

      await nftContract.addToWhitelist(whitelistAddresses.map((s) => s.address));

      for (let i = 0; i < 10; i++) {
        await nftContract.connect(whitelistAddresses[i]).mint(5, { value: PRICE * 5n });
      }

      const additionalWallets = [];
      for (let i = 0; i < 10; i++) {
        const wallet = ethers.Wallet.createRandom().connect(ethers.provider);
        await signers[0].sendTransaction({
          to: wallet.address,
          value: ethers.parseEther("1"),
        });
        additionalWallets.push(wallet);
      }

      await nftContract.addToWhitelist(additionalWallets.map((w) => w.address));

      for (let i = 0; i < 10; i++) {
        await nftContract.connect(additionalWallets[i]).mint(5, { value: PRICE * 5n });
      }

      await nftContract.addToWhitelist([whitelistAddresses[0].address]);

      await expect(nftContract.connect(whitelistAddresses[0]).mint(1, { value: PRICE })).to.be.revertedWith(
        "Exceeds max supply"
      );
    });
  });

  describe("Withdraw", function () {
    it("Should allow owner to withdraw balance", async () => {
      await nftContract.addToWhitelist([addr1.address]);
      await nftContract.connect(addr1).mint(2, { value: PRICE * 2n });

      const initialBalance = await ethers.provider.getBalance(deployer.address);

      const tx = await nftContract.withdraw();
      const receipt = await tx.wait();
      const gasUsed = receipt!.gasUsed * receipt!.gasPrice!;

      const finalBalance = await ethers.provider.getBalance(deployer.address);
      const received = finalBalance - initialBalance;

      expect(received + gasUsed).to.equal(PRICE * 2n);
    });

    it("Should fail if non-owner tries to withdraw", async () => {
      await expect(nftContract.connect(addr1).withdraw()).to.be.revertedWithCustomError(
        nftContract,
        "OwnableUnauthorizedAccount"
      );
    });
  });
});
