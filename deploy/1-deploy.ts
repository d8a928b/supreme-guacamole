import { HardhatRuntimeEnvironment } from "hardhat/types";
import { DeployFunction } from "hardhat-deploy/types";

const func: DeployFunction = async function (hre: HardhatRuntimeEnvironment) {
  const { deployments, getNamedAccounts, ethers } = hre;
  const { deploy, get } = deployments;
  const { deployer } = await getNamedAccounts();

  console.log("=========================");
  console.log("Deploy NFT");
  console.log("=========================");

  const nft = await deploy("NFT", {
    from: deployer,
    log: true,
    autoMine: true,
    args: [],
  });

  console.log("=========================");
  console.log("Deploy WhitelistSale");
  console.log("=========================");

  const whitelistSale = await deploy("WhitelistSale", {
    from: deployer,
    log: true,
    autoMine: true,
    args: [nft.address],
  });

  console.log("=========================");
  console.log("Granting minting role to WhitelistSale");
  console.log("=========================");

  const nftContract = await ethers.getContractAt("NFT", nft.address);
  const tx = await nftContract.setMinter(whitelistSale.address);
  await tx.wait();

  console.log("✅ Minter set successfully");
};

func.tags = ["deploy"];
export default func;
