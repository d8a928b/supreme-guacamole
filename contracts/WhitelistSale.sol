// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";

interface INFTCollection {
    function mintTo(address to, uint256 quantity) external;
}

contract WhitelistSale is Ownable {
    using MerkleProof for bytes32[];

    INFTCollection public nft;
    bytes32 public merkleRoot;

    uint256 public constant MAX_PER_WALLET = 5;
    uint256 public constant PRICE_PER_NFT = 0.003 ether;

    uint256 public whitelistEndTime;

    mapping(address => uint256) public mintedPerWallet;

    constructor(address nftAddress, uint256 _whitelistDurationInSeconds)
        Ownable(msg.sender)
    {
        nft = INFTCollection(nftAddress);
        whitelistEndTime = block.timestamp + _whitelistDurationInSeconds;
    }

    function setMerkleRoot(bytes32 root) external onlyOwner {
        merkleRoot = root;
    }

    function mint(uint256 quantity, bytes32[] calldata proof) external payable {
        require(quantity > 0, "Cannot mint 0");
        require(
            mintedPerWallet[msg.sender] + quantity <= MAX_PER_WALLET,
            "Exceeds wallet limit"
        );

        bool isWhitelistPhase = block.timestamp <= whitelistEndTime;

        if (isWhitelistPhase) {
            require(
                _verifyWhitelist(msg.sender, proof),
                "Invalid Merkle Proof"
            );
            require(msg.value == 0, "Whitelist mint is free");
        } else {
            require(
                msg.value == quantity * PRICE_PER_NFT,
                "Incorrect ETH value"
            );
        }

        mintedPerWallet[msg.sender] += quantity;
        nft.mintTo(msg.sender, quantity);
    }

    function _verifyWhitelist(address user, bytes32[] calldata proof)
        internal
        view
        returns (bool)
    {
        bytes32 leaf = keccak256(abi.encodePacked(user));
        return proof.verify(merkleRoot, leaf);
    }

    function withdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
}
