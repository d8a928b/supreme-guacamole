import json
import time
import hashlib
from eth_account import Account
from web3 import Web3
from eth_utils import keccak, to_bytes, to_hex

# Connect to network
w3 = Web3(Web3.HTTPProvider("https://sepolia.infura.io/v3/8ff3cfdd147a4b95916b75d2ba88f391"))  # Change to your RPC

# === Replace with your deployed addresses and ABIs ===
NFT_COLLECTION_ADDRESS = "0xee4A9F0f8271aB7fe7c245d2aA566E1b3A12CF51"
WHITELIST_SALE_ADDRESS = "0xcb0807A1262d60a94D6D0a956fe085acB4fEf6fF"
OWNER_PRIVATE_KEY = "5dd83e56f4c038272fcb82a205bf5374fc092e30e9c9bc871e76bc7d76e5c2e8"

with open("NFTCollection.json") as f:
    nft_abi = json.load(f)["abi"]

with open("WhitelistSale.json") as f:
    sale_abi = json.load(f)["abi"]

nft = w3.eth.contract(address=NFT_COLLECTION_ADDRESS, abi=nft_abi)
sale = w3.eth.contract(address=WHITELIST_SALE_ADDRESS, abi=sale_abi)

# === Helper: keccak leaf ===
def hash_leaf(addr):
    return keccak(to_bytes(hexstr=w3.to_checksum_address(addr).lower()))

# === Manual Merkle Tree ===
def build_merkle_tree(leaves):
    tree = [leaves]
    while len(tree[-1]) > 1:
        level = []
        nodes = tree[-1]
        for i in range(0, len(nodes), 2):
            left = nodes[i]
            right = nodes[i+1] if i+1 < len(nodes) else nodes[i]
            combined = keccak(left + right)
            level.append(combined)
        tree.append(level)
    return tree

def get_proof(leaves, target_index):
    tree = build_merkle_tree(leaves)
    proof = []
    for level in tree[:-1]:
        is_right_node = target_index % 2
        sibling_index = target_index - 1 if is_right_node else target_index + 1
        if sibling_index < len(level):
            proof.append(level[sibling_index])
        else:
            proof.append(level[target_index])
        target_index //= 2
    return proof

def set_merkle_root(whitelist):
    leaves = [hash_leaf(a) for a in whitelist]
    root = build_merkle_tree(leaves)[-1][0]
    acct = Account.from_key(OWNER_PRIVATE_KEY)
    tx = sale.functions.setMerkleRoot(root).build_transaction({
        "from": acct.address,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "gas": 500000,
        "gasPrice": w3.to_wei("2", "gwei")
    })
    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print("Merkle root set:", to_hex(root))
    print("Tx:", tx_hash.hex())

def withdraw():
    acct = Account.from_key(OWNER_PRIVATE_KEY)
    tx = sale.functions.withdraw().build_transaction({
        "from": acct.address,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "gas": 100000,
        "gasPrice": w3.to_wei("2", "gwei")
    })
    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print("Withdraw initiated. Tx:", tx_hash.hex())

def mint(address, private_key, whitelist):
    leaves = [hash_leaf(a) for a in whitelist]
    index = whitelist.index(address)
    proof = get_proof(leaves, index)
    hex_proof = [to_hex(p) for p in proof]

    acct = Account.from_key(private_key)
    is_whitelist_phase = int(time.time()) <= sale.functions.whitelistEndTime().call()
    value = 0 if is_whitelist_phase else w3.to_wei("0.003", "ether")

    tx = sale.functions.mint(1, hex_proof).build_transaction({
        "from": acct.address,
        "nonce": w3.eth.get_transaction_count(acct.address),
        "value": value,
        "gas": 500000,
        "gasPrice": w3.to_wei("2", "gwei")
    })
    signed = acct.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print("Minted! Tx:", tx_hash.hex())

def balance(address):
    bal = nft.functions.balanceOf(address).call()
    print(f"{address} owns {bal} NFTs.")

# === Main console ===
def main():
    while True:
        print("\nSelect mode:")
        print("1. Owner - Set whitelist + Merkle root")
        print("2. Owner - Withdraw")
        print("3. User - Mint")
        print("4. User - Check NFT balance")
        print("0. Exit")

        choice = input("Choice: ").strip()

        if choice == "1":
            wl = input("Comma-separated whitelist addresses: ").split(",")
            whitelist = [w3.to_checksum_address(a.strip()) for a in wl]
            set_merkle_root(whitelist)

        elif choice == "2":
            withdraw()

        elif choice == "3":
            addr = input("Your address: ").strip()
            pkey = input("Your private key: ").strip()
            wl = input("Enter full whitelist used for Merkle tree: ").split(",")
            whitelist = [w3.to_checksum_address(a.strip()) for a in wl]
            mint(w3.to_checksum_address(addr), pkey, whitelist)

        elif choice == "4":
            addr = input("Address to check: ").strip()
            balance(w3.to_checksum_address(addr))

        elif choice == "0":
            break

        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
