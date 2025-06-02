# WalletAA

WalletAA is a blockchain wallet analytics platform that tracks EIP-7702 authorization transactions and provides real-time data analysis across multiple blockchain networks.

## 📂 Project Overview

- **`backend/`** - Contains Python scripts for fetching blockchain data, processing transactions, and managing SQLite databases across multiple networks (Mainnet, Sepolia, OP, Base, BSC)

- **`server/`** - Flask-based API server that provides RESTful endpoints for transactions, authorizers, relayers, and overview statistics with pagination and search capabilities

- **`website/`** - Modern React application built with Ant Design Pro, featuring real-time data visualization, multi-language support, and responsive design

## 🤝 How to Contribute

We welcome contributions from the community! There are several ways you can contribute to WalletAA:

### 1. Contributing Code Information

- Submit PRs to [code_info.json](./server/code_info.json) about details of different EIP-7702 delegated codes
  ```json
  {
    "address": "0x000000004f43c49e93c970e84001853a70923b03",
    "name": "Nexus",
    "provider": "Biconomy",
    "code": "https://vscode.blockscan.com/ethereum/0x000000004f43c49e93c970e84001853a70923b03",
    "repo": "https://github.com/bcnmy/nexus",
    "contractAccountStandard": "ERC-4337",
    "verificationMethod": "Custom Module Verification",
    "verificationMethodExtra": "ERC-7579",
    "batchCall": true,
    "batchCallExtra": "ERC7821",
    "executor": true,
    "executorExtra": "ERC7579",
    "receiveETH": true,
    "receiveNFT": true,
    "recovery": true,
    "recoveryExtra": "ERC-7579 Module",
    "sessionKey": true,
    "sessionKeyExtra": "ERC-7579 Moudle",
    "storage": "Name spaced storage",
    "storageExtra": "ERC-7201",
    "nativeETHApprovalAndTransfer": false,
    "hooks": true,
    "hooksExtra": "ERC-7579 Module",
    "signature": "Readable Typed Signatures for Smart Accounts",
    "signatureExtra": "ERC-7739",
    "txInitiationMethod": "ERC-4337, Modular Execution Environment (MEE)",
    "feePaymentMethod": "ERC-4337, Modular Execution Environment (MEE)",
    "upgradable": true,
    "upgradableExtra": "UUPS",
    "modularContractAccount": "ERC-7579",
    "moduleRegistry": "ERC-7484",
    "isContractAddress": true,
    "audit": true,
    "production": true,
    "usage": "account abstraction"
  }
  ```
- Help analyze the underlying implementation details of different EIP-7702 delegated codes
- Ensure all code information is accurate and up-to-date

### 2. Contributing Tag Information

- Submit PRs to [tag_info.json](./server/tag_info.json) about tags for different EIP-7702 delegated codes
  ```json
  {
    "tag": "ERC-4337",
    "functions": [
      "validateUserOp((address,uint256,bytes,bytes,bytes32,uint256,bytes32,bytes,bytes),bytes32,uint256)"
    ]
  }
  ```
- Help improve the automatic discovery features for different EIP-7702 delegated codes
- Ensure all code tags are accurate and up-to-date

### 3. Contributing to WalletAA Codebase

- Submit PRs for bug fixes, feature enhancements, or performance improvements
- Follow the existing code style and conventions
- Include appropriate tests and documentation
- Ensure all tests pass before submitting

For all contributions:

- Fork the repository
- Create a new branch for your changes
- Submit a pull request with a clear description of your changes
- Wait for review and address any feedback

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
