import { HardhatRuntimeEnvironment } from "hardhat/types";
import { DeployFunction } from "hardhat-deploy/types";

const func: DeployFunction = async function (hre: HardhatRuntimeEnvironment) {
  const { deployments, getNamedAccounts } = hre;
  const { deploy } = deployments;
  const { deployer } = await getNamedAccounts();

  console.log("====================");
  console.log("Deploy NFTWhitelistSale Contract");
  console.log("====================");

  await deploy("NFTWhitelistSale", {
    from: deployer,
    log: true,
    autoMine: true,
  });
};

func.tags = ["deploy"];
export default func;
