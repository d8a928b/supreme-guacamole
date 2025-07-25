import "@nomicfoundation/hardhat-ethers";
import "@nomicfoundation/hardhat-chai-matchers";
import { ethers } from "hardhat";
import { expect } from "chai";
import { SignerWithAddress } from "@nomicfoundation/hardhat-ethers/signers";
import { NFT, WhitelistSale } from "../typechain-types";

describe("WhitelistSale", function () {
  let deployer: SignerWithAddress, addr1: SignerWithAddress, addr2: SignerWithAddress, addr3: SignerWithAddress;
  let nft: NFT;
  let sale: WhitelistSale;

  const PRICE = ethers.parseEther("0.003");

  beforeEach(async () => {
    [deployer, addr1, addr2, addr3] = await ethers.getSigners();

    const NFTFactory = await ethers.getContractFactory("NFT");
    nft = (await NFTFactory.connect(deployer).deploy()) as NFT;

    const SaleFactory = await ethers.getContractFactory("WhitelistSale");
    sale = (await SaleFactory.connect(deployer).deploy(nft.getAddress())) as WhitelistSale;

    await nft.setMinter(sale.getAddress());
  });

  describe("Deployment", function () {
    it("Should set NFT name and symbol correctly", async () => {
      expect(await nft.name()).to.equal("WhitelistNFT");
      expect(await nft.symbol()).to.equal("WLNFT");
    });

    it("Should start with zero minted", async () => {
      expect(await nft.totalMinted()).to.equal(0n);
    });
  });

  describe("Whitelist Management", function () {
    it("Should allow owner to add and remove from whitelist", async () => {
      await sale.addToWhitelist([addr1.address, addr2.address]);
      expect(await sale.whitelist(addr1.address)).to.equal(true);
      expect(await sale.whitelist(addr2.address)).to.equal(true);

      await sale.removeFromWhitelist([addr1.address]);
      expect(await sale.whitelist(addr1.address)).to.equal(false);
    });

    it("Should revert if non-owner tries to modify whitelist", async () => {
      await expect(sale.connect(addr1).addToWhitelist([addr3.address])).to.be.revertedWithCustomError(
        sale,
        "OwnableUnauthorizedAccount"
      );
    });
  });

  describe("Minting", function () {
    beforeEach(async () => {
      await sale.addToWhitelist([addr1.address]);
    });

    it("Should mint NFTs correctly for whitelisted users", async () => {
      await sale.connect(addr1).mint(2, { value: PRICE * 2n });

      expect(await nft.totalMinted()).to.equal(2n);
      expect(await nft.balanceOf(addr1.address)).to.equal(2n);
    });

    it("Should fail if not whitelisted", async () => {
      await expect(sale.connect(addr2).mint(1, { value: PRICE })).to.be.revertedWith("Not whitelisted");
    });

    it("Should fail if sent incorrect ETH value", async () => {
      await expect(sale.connect(addr1).mint(1, { value: PRICE - 1n })).to.be.revertedWith("Incorrect ETH value");
    });

    it("Should fail if minting more than max per wallet", async () => {
      await sale.connect(addr1).mint(5, { value: PRICE * 5n });

      await expect(sale.connect(addr1).mint(1, { value: PRICE })).to.be.revertedWith("Exceeds wallet limit");
    });

    it("Should fail if minting exceeds max supply", async () => {
      const fundedWallets: SignerWithAddress[] = [];

      // Create and fund 20 wallets
      for (let i = 0; i < 20; i++) {
        const wallet = ethers.Wallet.createRandom().connect(ethers.provider);
        await deployer.sendTransaction({
          to: wallet.address,
          value: ethers.parseEther("1"), // fund enough ETH
        });
        fundedWallets.push(wallet);
      }

      const whitelistAddresses = fundedWallets.slice(0, 20);
      await sale.addToWhitelist(whitelistAddresses.map((w) => w.address));

      // Mint 5 NFTs per wallet (20 × 5 = 100)
      for (let i = 0; i < 20; i++) {
        await sale.connect(whitelistAddresses[i]).mint(5, { value: PRICE * 5n });
      }

      // Check total supply hit limit
      expect(await nft.totalMinted()).to.equal(100n);

      // Attempt to exceed supply with one more wallet
      const overflowWallet = ethers.Wallet.createRandom().connect(ethers.provider);
      await deployer.sendTransaction({
        to: overflowWallet.address,
        value: ethers.parseEther("1"),
      });

      await sale.addToWhitelist([overflowWallet.address]);

      await expect(sale.connect(overflowWallet).mint(1, { value: PRICE })).to.be.revertedWith("Exceeds max supply");
    });
  });

  describe("Withdraw", function () {
    it("Should allow owner to withdraw balance", async () => {
      await sale.addToWhitelist([addr1.address]);
      await sale.connect(addr1).mint(2, { value: PRICE * 2n });

      const initialBalance = await ethers.provider.getBalance(deployer.address);

      const tx = await sale.withdraw();
      const receipt = await tx.wait();
      const gasUsed = receipt!.gasUsed * receipt!.gasPrice!;

      const finalBalance = await ethers.provider.getBalance(deployer.address);
      const received = finalBalance - initialBalance;

      expect(received + gasUsed).to.equal(PRICE * 2n);
    });

    it("Should fail if non-owner tries to withdraw", async () => {
      await expect(sale.connect(addr1).withdraw()).to.be.revertedWithCustomError(sale, "OwnableUnauthorizedAccount");
    });
  });
});
