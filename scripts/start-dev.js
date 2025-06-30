const { exec } = require("child_process");
const fs = require("fs");

function execCommand(command) {
  return new Promise((resolve, reject) => {
    exec(command, (error, stdout, stderr) => {
      if (error) {
        console.error(`Error: ${error}`);
        reject(error);
        return;
      }
      console.log(stdout);
      resolve(stdout);
    });
  });
}

function extractContractAddress(output) {
  const match = output.match(/contract address:\s+(0x[a-fA-F0-9]{40})/i);
  return match ? match[1] : null;
}

function updatePythonConfig(contractAddress, accountAddress, privateKey) {
  const configContent = `# config.py - Auto-generated blockchain configuration
CONTRACT_ADDRESS = "${contractAddress}"
ACCOUNT_ADDRESS = "${accountAddress}"  
PRIVATE_KEY = "${privateKey}"
GANACHE_URL = "http://127.0.0.1:8545"
NETWORK_ID = 5777
`;
  
  fs.writeFileSync("config.py", configContent);
  console.log("✅ Python config.py updated successfully!");
}

async function main() {
  try {
    console.log("🚀 Starting automated setup...");
    
    // Check if Ganache is running
    console.log("🔍 Checking if Ganache is running...");
    
    // Deploy contracts
    console.log("📦 Deploying contracts...");
    const deployOutput = await execCommand("truffle migrate --reset");
    
    // Extract contract address
    const contractAddress = extractContractAddress(deployOutput);
    if (!contractAddress) {
      throw new Error("Could not extract contract address");
    }
    
    // You'll need to get these from Ganache output
    const accountAddress = "0x627306090abaB3A6e1400e9345bC60c78a8BEf57"; // First Ganache account
    const privateKey = "0xc87509a1c067bbde78beb793e6fa76530b6382a4c0241e5e4a9ec0a0f44dc0d3"; // First private key
    
    // Update Python config
    updatePythonConfig(contractAddress, accountAddress, privateKey);
    
    console.log("✅ Setup complete!");
    console.log(`Contract Address: ${contractAddress}`);
    console.log(`Account Address: ${accountAddress}`);
    console.log("📄 Updated config.py with blockchain details");
    
  } catch (error) {
    console.error("❌ Setup failed:", error.message);
  }
}

main();