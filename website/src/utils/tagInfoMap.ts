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
    description: 'ERC-4337 allows users to interact with smart contracts using a lightweight account interface instead of a traditional wallet. This standard is designed to improve security and usability by providing a more flexible and efficient way to interact with smart contracts.',
    link: 'https://eips.ethereum.org/EIPS/eip-4337'
  },
  'ERC-7579 Moduler': {
    color: 'purple',
    description: 'ERC-7579 allows developers to create smart contracts that can be extended with new functionality by installing modules. This standard is designed to improve security and usability by providing a more flexible and efficient way to interact with smart contracts.',
    link: 'https://eips.ethereum.org/EIPS/eip-7579'
  },
  'ERC-6900 Moduler': {
    color: 'purple',
    description: 'ERC-6900',
    link: 'https://eips.ethereum.org/EIPS/eip-6900'
  },
  'ERC-7821 Batch': {
    color: 'green',
    description: 'ERC-7821',
    link: 'https://eips.ethereum.org/EIPS/eip-7821'
  },
  'Batch': {
    color: 'green',
    description: 'Batch execution',
    link: 'https://eips.ethereum.org/'
  },
  'ERC-7914': {
    color: 'orange',
    description: 'ERC-7914',
    link: 'https://eips.ethereum.org/EIPS/eip-7914'
  },
  'ERC-1271': {
    color: 'cyan',
    description: 'ERC-1271',
    link: 'https://eips.ethereum.org/EIPS/eip-1271'
  },
  'ERC-721 Receiver': {
    color: 'magenta',
    description: 'ERC-721 Receiver',
    link: 'https://eips.ethereum.org/EIPS/eip-721'
  },
  'ERC-1155 Receiver': {
    color: 'magenta',
    description: 'ERC-1155 Receiver',
    link: 'https://eips.ethereum.org/EIPS/eip-1155'
  },
  'ERC-1967': {
    color: 'red',
    description: 'ERC-1967',
    link: 'https://eips.ethereum.org/EIPS/eip-1967'
  },
  'Proxy': {
    color: 'gold',
    description: 'Proxy',
    link: 'https://eips.ethereum.org/'
  },
  'ERC-165': {
    color: 'lime',
    description: 'ERC-165',
    link: 'https://eips.ethereum.org/EIPS/eip-165'
  },
  'ERC-7779': {
    color: 'volcano',
    description: 'ERC-7779',
    link: 'https://eips.ethereum.org/EIPS/eip-7779'
  },
  'ERC-7821 Execution': {
    color: 'green',
    description: 'ERC-7821',
    link: 'https://eips.ethereum.org/EIPS/eip-7821'
  },
  'ERC-1967 Proxy': {
    color: 'red',
    description: 'ERC-1967 Proxy',
    link: 'https://eips.ethereum.org/EIPS/eip-1967'
  },
  'UUPSUpgradeable': {
    color: 'pink',
    description: 'UUPSUpgradeable',
    link: 'https://eips.ethereum.org/'
  },
  'ERC-7579 Executor': {
    color: 'purple',
    description: 'ERC-7579 Executor',
    link: 'https://eips.ethereum.org/EIPS/eip-7579'
  },
  'ERC-7710 Delegation': {
    color: 'geekblue',
    description: 'ERC-7710 Delegation',
    link: 'https://eips.ethereum.org/EIPS/eip-7710'
  },
  'ERC-6900 Execution': {
    color: 'green',
    description: 'ERC-6900',
    link: 'https://eips.ethereum.org/EIPS/eip-6900'
  },
  'ERC-6551': {
    color: 'blue',
    description: 'ERC-6551',
    link: 'https://eips.ethereum.org/EIPS/eip-6551'
  },
  'Proto Account': {
    color: 'green',
    description: 'Proto Account',
    link: 'https://eips.ethereum.org/'
  }
};

export default tagInfoMap;
export type { TagInfo }; 