// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract NFTCollection is ERC721, Ownable {
    uint256 public totalMinted;
    uint256 public constant MAX_SUPPLY = 100;

    constructor() ERC721("WhitelistNFT", "WLNFT") Ownable(msg.sender) {}

    function mintTo(address to, uint256 quantity) external onlyOwner {
        require(totalMinted + quantity <= MAX_SUPPLY, "Exceeds max supply");

        for (uint256 i = 0; i < quantity; i++) {
            _safeMint(to, totalMinted);
            totalMinted++;
        }
    }
}
