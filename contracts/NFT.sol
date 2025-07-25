// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract NFT is ERC721, Ownable {
    uint256 public totalMinted;
    uint256 public constant MAX_SUPPLY = 100;

    address public minter;

    constructor() ERC721("WhitelistNFT", "WLNFT") Ownable(msg.sender) {}

    modifier onlyMinter() {
        require(msg.sender == minter, "Not authorized to mint");
        _;
    }

    function setMinter(address _minter) external onlyOwner {
        minter = _minter;
    }

    function mintTo(address to, uint256 quantity) external onlyMinter {
        require(totalMinted + quantity <= MAX_SUPPLY, "Exceeds max supply");

        for (uint256 i = 0; i < quantity; i++) {
            _safeMint(to, totalMinted);
            totalMinted++;
        }
    }
}
