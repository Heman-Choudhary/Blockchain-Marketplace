const Web3 = require('web3');

async function getAccounts() {
  const web3 = new Web3('http://127.0.0.1:8545');
  
  try {
    const accounts = await web3.eth.getAccounts();
    console.log("Available accounts:");
    accounts.forEach((account, index) => {
      console.log(`${index}: ${account}`);
    });
    return accounts;
  } catch (error) {
    console.error("Error getting accounts:", error.message);
    return [];
  }
}

getAccounts();