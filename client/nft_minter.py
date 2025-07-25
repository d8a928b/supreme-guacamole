import json
import os
from web3 import Web3
import getpass
from dotenv import load_dotenv



load_dotenv()
RPC_URL = os.getenv("RPC_URL")
NFT_ADDRESS = os.getenv("NFT_ADDRESS")
SALE_ADDRESS = os.getenv("SALE_ADDRESS")

print(RPC_URL,NFT_ADDRESS,SALE_ADDRESS)

with open("NFT.json") as f:
    nft_abi = json.load(f)["abi"]
with open("WhitelistSale.json") as f:
    sale_abi = json.load(f)["abi"]


w3 = Web3(Web3.HTTPProvider(RPC_URL))


PRIVATE_KEY = getpass.getpass("🔑 Enter your private key: ").strip()
account = w3.eth.account.from_key(PRIVATE_KEY)
ACCOUNT = account.address


nft = w3.eth.contract(address=NFT_ADDRESS, abi=nft_abi)
sale = w3.eth.contract(address=SALE_ADDRESS, abi=sale_abi)

OWNER = nft.functions.owner().call()
IS_OWNER = ACCOUNT.lower() == OWNER.lower()


def send_tx(tx):
    tx.update(
        {
            "nonce": w3.eth.get_transaction_count(ACCOUNT),
            "maxFeePerGas": w3.to_wei("2", "gwei"),
            "maxPriorityFeePerGas": w3.to_wei("1.5", "gwei"),
            "gas": 500000,
            "chainId": w3.eth.chain_id,
        }
    )
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"📤 Sent tx: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("✅ Transaction mined.")
    return receipt


def check_whitelist(addr):
    if IS_OWNER:
        print(f"🔍 Checking whitelist for: {addr}")
        is_whitelisted = sale.functions.isWhitelisted(addr).call()
        print(
            f"📌 {addr} is {'✅ whitelisted' if is_whitelisted else '❌ not whitelisted'}"
        )
    else:
        is_whitelisted = sale.functions.isWhitelisted(ACCOUNT).call()
        print(
            f"👤 You are {'✅ whitelisted' if is_whitelisted else '❌ not whitelisted'}"
        )


def check_minted_by_user(addr):
    minted = sale.functions.mintedPerWallet(addr).call()
    if IS_OWNER:
        print(f"🧾 {addr} has minted {minted} NFTs")
    else:
        print(f"🧾 You have minted {minted} NFTs")
    return minted


def mint(quantity):

    if not sale.functions.isWhitelisted(ACCOUNT).call():
        print("❌ You are not whitelisted. Cannot mint.")
        return

    max_per_wallet = sale.functions.MAX_PER_WALLET().call()
    price_per_nft = sale.functions.PRICE_PER_NFT().call()

    already_minted = check_minted_by_user(ACCOUNT)

    if already_minted + quantity > max_per_wallet:
        print(
            f"❌ You already minted {already_minted}, max per wallet is {max_per_wallet}"
        )
        return

    total_cost = price_per_nft * quantity
    print(f"💰 Total cost: {Web3.from_wei(total_cost, 'ether')} ETH")

    if input("Proceed? (y/n): ").lower() != "y":
        print("❌ Cancelled.")
        return

    tx = sale.functions.mint(quantity).build_transaction(
        {"from": ACCOUNT, "value": total_cost}
    )
    send_tx(tx)


def add_to_whitelist(addr):
    tx = sale.functions.addToWhitelist([addr]).build_transaction({"from": ACCOUNT})
    send_tx(tx)


def remove_from_whitelist(addr):
    tx = sale.functions.removeFromWhitelist([addr]).build_transaction({"from": ACCOUNT})
    send_tx(tx)


def total_minted():
    count = nft.functions.totalMinted().call()
    print(f"🎉 Total NFTs minted: {count}")


def withdraw():
    tx = sale.functions.withdraw().build_transaction({"from": ACCOUNT})
    send_tx(tx)


def menu():
    print(f"\n🔐 Logged in as: {ACCOUNT}")
    print(f"🧑‍💼 Role: {'OWNER' if IS_OWNER else 'USER'}")

    while True:
        print("\n=== NFT Whitelist Console ===")
        options = []

        options.append(
            (
                "Check Whitelist",
                lambda: check_whitelist(
                    input("Enter address to check: ").strip() if IS_OWNER else ACCOUNT
                ),
            )
        )

        if not IS_OWNER:
            options.append(
                ("Mint NFT", lambda: mint(int(input("How many NFTs to mint? "))))
            )

        if IS_OWNER:
            options.append(
                (
                    "Add to Whitelist (owner only)",
                    lambda: add_to_whitelist(input("Address to add: ").strip()),
                )
            )
            options.append(
                (
                    "Remove from Whitelist (owner only)",
                    lambda: remove_from_whitelist(input("Address to remove: ").strip()),
                )
            )
            options.append(("Total Minted", total_minted))
            options.append(("Withdraw ETH (owner only)", withdraw))
        else:
            options.append(("My Minted NFTs", lambda: check_minted_by_user(ACCOUNT)))

        options.append(("Exit", lambda: exit()))

        for idx, (label, _) in enumerate(options, start=1):
            print(f"{idx}. {label}")

        choice = input("Choose an option: ").strip()

        if choice.isdigit():
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(options):
                try:
                    options[choice_idx][1]()
                except Exception as e:

                    err_str = str(e)

                    if "insufficient funds" in err_str.lower():
                        print("❌ Insufficient funds!")
                    else:
                        print(f"❌ Error: {err_str}")
            else:
                print("❌ Invalid option.")
        else:
            print("❌ Invalid input.")


if __name__ == "__main__":
    menu()