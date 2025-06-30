import Web3 from 'web3';

let contract;
let accounts;

window.addEventListener('load', async () => {
  if (window.ethereum) {
    window.web3 = new Web3(window.ethereum);
    await ethereum.request({ method: 'eth_requestAccounts' });

    accounts = await web3.eth.getAccounts();
    const networkId = await web3.eth.net.getId();
    const contractData = await fetch('../build/contracts/Marketplace.json').then(res => res.json());
    const networkData = contractData.networks[networkId];

    if (networkData) {
      contract = new web3.eth.Contract(contractData.abi, networkData.address);
      loadProducts();
    } else {
      alert('Smart contract not deployed to detected network.');
    }
  } else {
    alert('Please install MetaMask to interact with this app.');
  }
});

document.getElementById('productForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const name = document.getElementById('name').value;
  const price = document.getElementById('price').value;

  await contract.methods.createProduct(name, price).send({ from: accounts[0] });
  loadProducts();
});

async function loadProducts() {
  const productsDiv = document.getElementById('products');
  productsDiv.innerHTML = ''; // Clear existing products

  const count = await contract.methods.productCount().call(); // Get the number of products
  for (let i = 1; i <= count; i++) {
    const product = await contract.methods.products(i).call(); // Get product details
    if (!product.sold) {
      const div = document.createElement('div');
      div.innerHTML = `
        <p><strong>${product.name}</strong> - Price: ${product.price} Wei</p>
        <button onclick="buyProduct(${product.id}, ${product.price})">Buy</button>
      `;
      productsDiv.appendChild(div);
    }
  }
}

async function buyProduct(id, price) {
  const accounts = await web3.eth.getAccounts(); // Get the user's account
  await contract.methods.purchaseProduct(id).send({ from: accounts[0], value: price });
  loadProducts(); // Reload the products after purchase
}
