const { MerkleTree } = require('merkletreejs');
const keccak256 = require('keccak256');

const whitelistAddresses = [
  "0x057aFd2552c7F03B3A7dD58993aae61a3278b53D", // whitelisted addresses
];

const leafNodes = whitelistAddresses.map(addr => keccak256(addr));
const merkleTree = new MerkleTree(leafNodes, keccak256, { sortPairs: true });

console.log("Merkle Root:", merkleTree.getHexRoot());

// For a specific user:
const claimingAddress = "0x057aFd2552c7F03B3A7dD58993aae61a3278b53D";
const proof = merkleTree.getHexProof(keccak256(claimingAddress));
