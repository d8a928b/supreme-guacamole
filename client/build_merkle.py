import json
from eth_utils import keccak, to_checksum_address
from typing import List

def keccak256(data: bytes) -> bytes:
    return keccak(data)

def hash_leaf(address: str) -> bytes:
    """Hash a single address as a leaf node"""
    address = to_checksum_address(address)
    return keccak256(bytes.fromhex(address[2:].lower().zfill(40)))

def build_merkle_tree(leaves: List[bytes]) -> List[List[bytes]]:
    tree = [leaves]
    while len(tree[-1]) > 1:
        level = tree[-1]
        new_level = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i+1] if i + 1 < len(level) else level[i]
            new_level.append(keccak256(left + right))
        tree.append(new_level)
    return tree

def get_proof(index: int, tree: List[List[bytes]]) -> List[str]:
    proof = []
    for level in tree[:-1]:
        pair_index = index ^ 1
        if pair_index < len(level):
            proof.append("0x" + level[pair_index].hex())
        index //= 2
    return proof

def main():
    # Replace with your actual whitelist addresses
    addresses = [
        "0x057aFd2552c7F03B3A7dD58993aae61a3278b53D"
    ]

    leaves = [hash_leaf(addr) for addr in addresses]
    merkle_tree = build_merkle_tree(leaves)
    merkle_root = merkle_tree[-1][0]

    print(f"Merkle Root: 0x{merkle_root.hex()}")

    # Optionally generate and save Merkle proofs
    proofs = {}
    for i, addr in enumerate(addresses):
        proof = get_proof(i, merkle_tree)
        proofs[to_checksum_address(addr)] = proof

    with open("merkle_proofs.json", "w") as f:
        json.dump(proofs, f, indent=2)

    print("Merkle proofs saved to merkle_proofs.json")

if __name__ == "__main__":
    main()
