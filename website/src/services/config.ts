// 定义支持的链类型
export type ChainType = 'mainnet' | 'sepolia';

// 默认链
export const DEFAULT_CHAIN: ChainType = 'mainnet';

// 链配置接口
interface ChainConfig {
  BASE_URL: string;
  EXPLORER_URL: string;
  CHAIN_ID: number;
}

// 各链的配置
export const CHAIN_CONFIGS: Record<ChainType, ChainConfig> = {
  mainnet: {
    BASE_URL: '/api-mainnet',
    EXPLORER_URL: 'https://etherscan.io',
    CHAIN_ID: 1,
  },
  sepolia: {
    BASE_URL: '/api-sepolia',
    EXPLORER_URL: 'https://sepolia.etherscan.io',
    CHAIN_ID: 11155111,
  },
};

// 获取当前链类型
export function getCurrentChain(): ChainType {
  const urlParams = new URLSearchParams(window.location.search);
  const chain = urlParams.get('chain') as ChainType;
  return chain && Object.keys(CHAIN_CONFIGS).includes(chain) ? chain : DEFAULT_CHAIN;
}

// 获取当前链配置
export function getChainConfig(): ChainConfig {
  const currentChain = getCurrentChain();
  return CHAIN_CONFIGS[currentChain];
}

// 获取带有chain参数的URL，当chain为默认值时不添加参数
export function getUrlWithChain(url: string): string {
  const currentChain = getCurrentChain();
  
  // 如果是默认链，不添加参数
  if (currentChain === DEFAULT_CHAIN) {
    return url;
  }
  
  const urlObj = new URL(url, window.location.origin);
  urlObj.searchParams.set('chain', currentChain);
  return urlObj.pathname + urlObj.search;
} 