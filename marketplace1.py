import streamlit as st
from web3 import Web3
import json

st.set_page_config(page_title="Blockchain Marketplace", page_icon="🛒")

# Initialize session state for persistency
if 'purchased_products' not in st.session_state:
    st.session_state.purchased_products = []

# Connect to Ganache
ganache_url = "http://127.0.0.1:8545"
w3 = Web3(Web3.HTTPProvider(ganache_url))

# Show connection status
if w3.is_connected():
    st.sidebar.success("✅ Connected to Ganache")
else:
    st.sidebar.error("❌ Failed to connect to Ganache")

# Hardcode your Ganache Account
account_address = "0x0eC59eb07c1E1A6e78F945A22a45c75e7425fa29"  # your ganache account address
private_key = "0a5478dc1ee35a46db618b4f8fa186aaa2a86f888d386849793b78c0c0bf6eb7"  # private key WITHOUT 0x if needed

st.sidebar.write(f"**Account:** {account_address[:10]}...")

# Load contract ABI and address
try:
    with open('build/contracts/Marketplace.json') as f:
        contract_data = json.load(f)

    contract_abi = contract_data['abi']
    contract_address = "0xC30AcfB53b2943250aD8A7F9777b8b3f54F99C82" # deploy_marketplace.js contract address after running truffle

    if contract_abi is None or contract_address is None:
        raise ValueError("Contract ABI or Address is missing")
        
    # Initialize contract
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    st.sidebar.success("✅ Contract loaded")
    
except Exception as e:
    st.sidebar.error(f"❌ Failed to load contract: {e}")
    st.stop()

# Add this function to refresh contract state
def reload_contract_state():
    # Reinitialize the web3 connection
    global w3, contract
    w3 = Web3(Web3.HTTPProvider(ganache_url))
    
    # Check connection
    if not w3.is_connected():
        st.error("❌ Failed to connect to Ganache. Make sure it's running on the specified URL.")
        return False
    
    # Reinitialize contract
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
    st.success("✅ Contract state reloaded!")
    return True

# Add a reload button in the sidebar
if st.sidebar.button("Reload Contract State"):
    reload_contract_state()

# Convert ETH to Wei manually
def eth_to_wei(eth_amount):
    return int(Web3.to_wei(eth_amount, 'ether'))

# Add product function
def add_product():
    st.subheader("📦 Add New Product")
    
    with st.form(key='product_form'):
        name = st.text_input("Product Name")
        price = st.number_input("Price (ETH)", min_value=0.001, step=0.001, format="%.3f")

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
                    'gasPrice': Web3.to_wei('2', 'gwei'),
                    'nonce': w3.eth.get_transaction_count(account_address),
                })

                signed_tx = w3.eth.account.sign_transaction(tx, private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                
                with st.spinner("Adding product to blockchain..."):
                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if receipt.status == 1:
                    st.success(f"Product added successfully! Transaction Hash: {tx_hash.hex()}")
                    # Update session state to trigger a page refresh
                    st.session_state.product_added = True
                    st.session_state.update({"product_added": True})
                else:
                    st.error("Transaction failed!")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")

# Improved display_products function
def display_products():
    st.subheader("🛒 Available Products")
    
    try:
        # Fetch available products from the contract
        ids, names, prices, sellers = contract.functions.getAvailableProducts().call()
        
        if not ids:  # Check if no products are available
            st.info("No available products. Be the first to add one!")
            return
        
        st.write(f"Found {len(ids)} available products")

        for i in range(len(ids)):
            # Create a nice card-like display for each product
            with st.container():
                st.markdown("---")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    ### {names[i]}
                    **Price:** {Web3.from_wei(prices[i], 'ether')} ETH  
                    **Seller:** {sellers[i][:10]}...
                    """)
                
                with col2:
                    if st.button(f"Buy Now", key=f"buy_{ids[i]}"):
                        purchase_product(ids[i], prices[i])

    except Exception as e:
        st.error(f"An error occurred: {e}")
        import traceback
        st.code(traceback.format_exc())


# Purchase a product with debugging
def purchase_product(product_id, price):
    try:
        # Get the product and check if it's already sold
        product = contract.functions.getProductById(product_id).call()
        
        # Debug information
        with st.expander("Product Details (Debug)"):
            st.write(f"ID: {product[0]}")
            st.write(f"Name: {product[1]}")
            st.write(f"Price: {product[2]}")
            st.write(f"Seller: {product[3]}")
            st.write(f"Buyer: {product[4]}")
            st.write(f"Is Sold: {product[5]}")

        # Check if product is already sold
        if product[5]:  # This checks the isSold field
            st.warning("⚠️ This product has already been sold.")
            return

        # Continue with purchase if not sold
        txn = contract.functions.purchaseProduct(product_id).build_transaction({
            'from': account_address,
            'value': price,  # Make sure price is in wei
            'gas': 2000000,
            'gasPrice': Web3.to_wei('2', 'gwei'),
            'nonce': w3.eth.get_transaction_count(account_address),
        })

        signed_tx = w3.eth.account.sign_transaction(txn, private_key)
        
        with st.spinner('Processing purchase... ⏳'):
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # Check transaction status
            if receipt.status == 1:
                st.success(f'✅ Product purchased successfully! Transaction Hash: {tx_hash.hex()}')
                # Add to session state for persistence
                st.session_state.purchased_products.append(product)
                # Update the session state to force refresh
                st.session_state.update({"purchase_made": True})

            else:
                st.error("❌ Transaction failed! Check Ganache logs for details.")

    except Exception as e:
        st.error(f"❌ An error occurred during purchase: {e}")
        # Show more detailed error information
        import traceback
        st.code(traceback.format_exc())


# Display purchase history using contract data
def display_my_purchases():
    st.subheader("📜 Your Purchase History")

    try:
        # Get purchases from blockchain
        purchased_products = contract.functions.getMyPurchases().call({'from': account_address})

        if not purchased_products:
            st.info("You haven't made any purchases yet.")
            return

        for product in purchased_products:
            st.markdown(f"""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 10px; color: black;">
                <h3>{product[1]}</h3>
                <p><strong>Price:</strong> {Web3.from_wei(product[2], 'ether')} ETH</p>
                <p><strong>Seller:</strong> {product[3][:10]}...</p>
                <p><strong>Status:</strong> Purchased ✅</p>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred while fetching purchase history: {e}")
        import traceback
        st.code(traceback.format_exc())


# Main Page Layout with Tabs
def main():
    st.title("🛒 Blockchain Marketplace")
    
    tab1, tab2, tab3 = st.tabs(["Browse Products", "My Purchases", "Sell Product"])
    
    with tab1:
        display_products()
    
    with tab2:
        display_my_purchases()
    
    with tab3:
        add_product()


if __name__ == "__main__":
    main()