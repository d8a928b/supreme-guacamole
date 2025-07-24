import json
from web3 import Web3
import getpass
import os
from dotenv import load_dotenv

load_dotenv()


RPC_URL = os.getenv("RPC_URL")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

with open("NFTWhitelistSale.json", "r") as f:
    contract_abi = json.load(f)["abi"]

w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)


def connect_wallet():
    private_key = getpass.getpass("Enter your private key: ")
    account = w3.eth.account.from_key(private_key)
    print(f"Connected!")
    return account


def send_tx(account, function_call, value=0):
    try:
        nonce = w3.eth.get_transaction_count(account.address)
        tx = function_call.build_transaction(
            {
                "from": account.address,
                "value": value,
                "nonce": nonce,
                "gas": 300000,
                "gasPrice": w3.to_wei("20", "gwei"),
            }
        )
        signed_tx = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"Sent tx: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print("Success!" if receipt.status == 1 else "Not success!")
        return receipt

    except Exception as e:
        message = str(e)
        if "insufficient funds" in message:
            print("Insufficient funds!")
        else:
            print(f"Not success: {message}")
        return None


def owner_menu(account):
    while True:
        print("\n--- OWNER MENU ---")
        print("1. Add to whitelist")
        print("2. Remove from whitelist")
        print("3. Withdraw funds")
        print("0. Back")
        choice = input("Choose: ")
        if choice == "1":
            addresses = [
                addr.strip() for addr in input("Comma-separated addresses: ").split(",")
            ]

            already_whitelisted = [
                addr for addr in addresses if contract.functions.whitelist(addr).call()
            ]
            if already_whitelisted:
                print(f"{already_whitelisted} already in the whitelist!")
                continue

            tx = contract.functions.addToWhitelist(addresses)
            send_tx(account, tx)
        elif choice == "2":
            addresses = [
                addr.strip() for addr in input("Comma-separated addresses: ").split(",")
            ]

            for addr in addresses:
                if not contract.functions.whitelist(addr).call():
                    print(f"{addr} not in the whitelist!")
                    continue
            tx = contract.functions.removeFromWhitelist(addresses)
            send_tx(account, tx)
        elif choice == "3":
            tx = contract.functions.withdraw()
            send_tx(account, tx)
        elif choice == "0":
            break


def user_menu(account):
    while True:
        print("\n--- USER MENU ---")
        print("1. Mint NFT")
        print("2. View my NFTs")
        print("0. Back")
        choice = input("Choose: ")
        if choice == "1":
            try:
                qty = int(input("How many NFTs to mint? "))
            except ValueError:
                print("Invalid!")
                continue

            if qty <= 0:
                print("Must mint at least 1 NFT!")
                continue

            max_per_wallet = contract.functions.MAX_PER_WALLET().call()
            max_supply = contract.functions.MAX_SUPPLY().call()
            minted_by_user = contract.functions.mintedPerWallet(account.address).call()
            total_minted = contract.functions.totalMinted().call()

            if minted_by_user + qty > max_per_wallet:
                print(f"Already minted {minted_by_user}, max allowed {max_per_wallet}!")
                continue

            if total_minted + qty > max_supply:
                print(
                    f"Total supply currently {total_minted}, max allowed {max_supply}!"
                )
                continue

            price_per_nft = contract.functions.PRICE_PER_NFT().call()
            total_price = price_per_nft * qty

            tx = contract.functions.mint(qty)
            receipt = send_tx(account, tx, value=total_price)

            if receipt is None:
                print("Not success!")
        elif choice == "2":
            balance = contract.functions.balanceOf(account.address).call()
            print(f"You own {balance} NFTs.")
        elif choice == "0":
            break


def main():
    print("NFTWhitelistSale Console")
    while True:
        role = input("Login as (owner/user): ").strip().lower()

        if role not in ["owner", "user"]:
            print("Invalid role.")
            continue

        account = connect_wallet()

        if role == "owner":
            contract_owner = contract.functions.owner().call()
            if account.address != contract_owner:
                print("Not contract owner!")
                continue
            owner_menu(account)

        elif role == "user":
            is_whitelisted = contract.functions.whitelist(account.address).call()
            if not is_whitelisted:
                print("Not whitelisted!")
                continue
            user_menu(account)
        else:
            print("Invalid role!")


if __name__ == "__main__":
    main()
