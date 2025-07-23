// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract NFTWhitelistSale is ERC721, Ownable {
    uint256 public constant MAX_SUPPLY = 100;
    uint256 public constant MAX_PER_WALLET = 5;
    uint256 public constant PRICE_PER_NFT = 0.003 ether;

    mapping(address => bool) public whitelist;
    mapping(address => uint256) public mintedPerWallet;
    uint256 public totalMinted;

    constructor() ERC721("WhitelistNFT", "WLNFT") Ownable(msg.sender) {}

    function addToWhitelist(address[] calldata users) external onlyOwner {
        for (uint256 i = 0; i < users.length; i++) {
            whitelist[users[i]] = true;
        }
    }

    function removeFromWhitelist(address[] calldata users) external onlyOwner {
        for (uint256 i = 0; i < users.length; i++) {
            whitelist[users[i]] = false;
        }
    }

    function mint(uint256 quantity) external payable {
        require(whitelist[msg.sender], "Not whitelisted");
        require(quantity > 0, "Cannot mint 0");
        require(totalMinted + quantity <= MAX_SUPPLY, "Exceeds max supply");
        require(
            mintedPerWallet[msg.sender] + quantity <= MAX_PER_WALLET,
            "Exceeds wallet limit"
        );
        require(msg.value == PRICE_PER_NFT * quantity, "Incorrect ETH value");

        mintedPerWallet[msg.sender] += quantity;

        for (uint256 i = 0; i < quantity; i++) {
            _safeMint(msg.sender, totalMinted);
            totalMinted++;
        }
    }

    function withdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
}
