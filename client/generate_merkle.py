import json
from eth_utils import keccak, to_checksum_address
from eth_hash.auto import keccak as keccak256


def keccak_leaf(address: str) -> bytes:
    return keccak256(bytes.fromhex(address[2:].lower().zfill(40)))


def build_merkle_tree(leaves: list[bytes]) -> list[list[bytes]]:
    tree = [leaves]
    while len(tree[-1]) > 1:
        layer = []
        nodes = tree[-1]
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i + 1] if i + 1 < len(nodes) else nodes[i]
            layer.append(keccak256(left + right))
        tree.append(layer)
    return tree


def get_proof(tree: list[list[bytes]], index: int) -> list[str]:
    proof = []
    for level in tree[:-1]:
        sibling_index = index ^ 1
        if sibling_index < len(level):
            proof.append("0x" + level[sibling_index].hex())
        index //= 2
    return proof


def main():
    # STEP 1: Load addresses (edit this list or load from file)
    with open("addresses.txt", "r") as f:
        raw_addresses = [line.strip() for line in f if line.strip()]

    addresses = [to_checksum_address(addr) for addr in raw_addresses]
    leaves = [keccak_leaf(addr) for addr in addresses]

    # STEP 2: Build tree
    tree = build_merkle_tree(leaves)
    root = tree[-1][0]
    print(f"\n✅ Merkle Root: 0x{root.hex()}\n")

    # STEP 3: Generate proofs
    proof_map = {}
    for i, addr in enumerate(addresses):
        proof = get_proof(tree, i)
        proof_map[addr.lower()] = proof

    # STEP 4: Write output
    with open("merkletree.json", "w") as f:
        json.dump(proof_map, f, indent=2)

    with open("merkleroot.txt", "w") as f:
        f.write("0x" + root.hex())

    print("✅ merkletree.json and merkleroot.txt saved!")


if __name__ == "__main__":
    main()
