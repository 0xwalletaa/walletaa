/**
 * 标签信息映射 - 为不同标签定义颜色、描述和链接
 */
interface TagInfo {
  color: string;
  description: string;
  link: string;
}

const tagInfoMap: Record<string, TagInfo> = {
  'ERC-4337': {
    color: 'blue',
    description: 'An account abstraction proposal which completely avoids consensus-layer protocol changes, instead relying on higher-layer infrastructure',
    link: 'https://eips.ethereum.org/EIPS/eip-4337'
  },
  'ERC-7579 Moduler': {
    color: 'purple',
    description: 'Modular smart account interfaces and behavior for interoperability with minimal restrictions for accounts and modules',
    link: 'https://eips.ethereum.org/EIPS/eip-7579'
  },
  'ERC-6900 Moduler': {
    color: 'purple',
    description: 'Interfaces for smart contract accounts and modules, optionally supporting upgradability and introspection',
    link: 'https://eips.ethereum.org/EIPS/eip-6900'
  },
  'ERC-7821 Execution': {
    color: 'green',
    description: 'A minimal batch executor interface for delegations',
    link: 'https://eips.ethereum.org/EIPS/eip-7821'
  },
  'ERC-6900 Execution': {
    color: 'green',
    description: 'Execution interfaces of ERC-6900',
    link: 'https://eips.ethereum.org/EIPS/eip-6900'
  },
  'Batch': {
    color: 'green',
    description: 'Execute a sequence of operations in one atomic transaction.',
    link: ''
  },
  'ERC-7914': {
    color: 'orange',
    description: 'An Interface for Transfer From Native',
    link: 'https://docs.uniswap.org/contracts/smart-wallet/advanced-usage/erc-7914'
  },
  'ERC-1271': {
    color: 'cyan',
    description: 'Standard way to verify a signature when the account is a smart contract',
    link: 'https://eips.ethereum.org/EIPS/eip-1271'
  },
  'ERC-721 Receiver': {
    color: 'magenta',
    description: 'Handle the Receipt of an ERC-721 NFT',
    link: 'https://eips.ethereum.org/EIPS/eip-721'
  },
  'ERC-1155 Receiver': {
    color: 'magenta',
    description: 'Handle the Receipt of an ERC-1155 NFT',
    link: 'https://eips.ethereum.org/EIPS/eip-1155'
  },
  'ERC-1967 Proxy': {
    color: 'red',
    description: 'A consistent location where proxies store the address of the logic contract they delegate to, as well as other proxy-specific information.',
    link: 'https://eips.ethereum.org/EIPS/eip-1967'
  },
  'Proxy': {
    color: 'red',
    description: 'A Bytecode Redirect Implementation',
    link: ''
  },
  'ERC-1822 UUPS': {
    color: 'red',
    description: 'Universal Upgradeable Proxy Standard (UUPS)',
    link: 'https://eips.ethereum.org/EIPS/eip-1822'
  },
  'ERC-165': {
    color: 'lime',
    description: 'Standard Interface Detection',
    link: 'https://eips.ethereum.org/EIPS/eip-165'
  },
  'ERC-7779': {
    color: 'volcano',
    description: 'Interface for delegated externally owned accounts to enable better redelegation between wallets.',
    link: 'https://eips.ethereum.org/EIPS/eip-7779'
  },
  'ERC-7579 Executor': {
    color: 'geekblue',
    description: 'Interfaces for executing transactions on behalf of the smart account',
    link: 'https://eips.ethereum.org/EIPS/eip-7579'
  },
  'ERC-7710 Delegation': {
    color: 'geekblue',
    description: 'Interfaces for consistently delegating capabilities to other contracts or EOAs.',
    link: 'https://eips.ethereum.org/EIPS/eip-7710'
  },
  'ERC-6551': {
    color: 'blue',
    description: 'An interface and registry for smart contract accounts owned by non-fungible tokens',
    link: 'https://eips.ethereum.org/EIPS/eip-6551'
  },
  'Proto Account': {
    color: 'blue',
    description: 'All-in-one EIP-7702 powered account contract, coupled with Porto',
    link: 'https://github.com/ithacaxyz/account/tree/main'
  }
};

export default tagInfoMap;
export type { TagInfo }; 