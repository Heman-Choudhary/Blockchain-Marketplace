import streamlit as st
import json
from web3 import Web3
import os

# Connect to Ethereum
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Hardcode your Ganache Account
account_address = "0x7f5e1A40Dd86651A023692Cd538E428256134d2B"   # your ganache account address
private_key = "6f0ef8a37f92f74e8cc4edf003f7c1cad08a19fd1085e999aeaf6e0e8cdc789b"  # private key WITHOUT 0x if needed

st.write(f"Using account: {account_address}")

# Load contract ABI and address
with open('build/contracts/Marketplace.json') as f:
    contract_data = json.load(f)

contract_abi = contract_data['abi']
contract_address = "0xfdaf7bb3FB942d159a432BDa6bEaC90790494E79"

if contract_abi is None or contract_address is None:
    raise ValueError("Contract ABI or Address is missing")

# Initialize contract
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# Convert ETH to Wei manually
def eth_to_wei(eth_amount):
    return int(eth_amount * 10**18)

# Add product function (Streamlit input instead of console input)
def add_product():
    st.subheader("Add Product")
    
    with st.form(key='product_form'):
        name = st.text_input("Product Name")
        price = st.number_input("Price (ETH)", min_value=0.01, step=0.01)

        submit_button = st.form_submit_button("Add Product")

        if submit_button:
            if not name or price <= 0:
                st.error("Please provide valid product details.")
                return

            price_in_wei = eth_to_wei(price)

            try:
                tx = contract.functions.createProduct(name, price_in_wei).build_transaction({
                    'from': account_address,
                    'gas': 2000000,
                    'gasPrice': Web3.to_wei('20', 'gwei'),
                    'nonce': w3.eth.get_transaction_count(account_address),
                })

                signed_tx = w3.eth.account.sign_transaction(tx, private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                st.success(f"Product added successfully! Transaction Hash: {tx_hash.hex()}")
            except Exception as e:
                st.error(f"An error occurred: {e}")

def display_products():
    st.subheader("Available Products")
    
    try:
        product_count = contract.functions.product_count().call()
        
        if product_count == 0:
            st.info("No products available.")
            return
        
        for i in range(1, product_count + 1):
            product = contract.functions.products(i).call()
            if not product[4]:  # If not sold
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{product[1]}** - {Web3.from_wei(product[2], 'ether')} ETH")
                with col2:
                    buy_button = st.button(f'Buy {product[1]}', key=i)

                if buy_button:
                    purchase_product(i)
    except Exception as e:
        st.error(f"An error occurred while fetching products: {e}")

def purchase_product(product_id):
    try:
        product = contract.functions.products(product_id).call()

        if product[4]:  # Already sold
            st.warning("This product has already been sold.")
            return
        
        tx = contract.functions.purchaseProduct(product_id).build_transaction({
            'from': account_address,
            'value': product[2],
            'gas': 2000000,
            'gasPrice': Web3.to_wei('20', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account_address),
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        st.success(f'Product purchased successfully! Transaction Hash: {tx_hash.hex()}')

    except Exception as e:
        st.error(f"An error occurred: {e}")

# Streamlit UI main function
def main():
    st.title('Blockchain Marketplace')

    st.markdown("""
        ## Welcome to the Blockchain Marketplace!  
        Buy and sell products in a decentralized manner.
    """)

    option = st.selectbox("What would you like to do?", ["View Products", "Add Product"])

    if option == "View Products":
        display_products()
    elif option == "Add Product":
        add_product()

if __name__ == '__main__':
    main()
