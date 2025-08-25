import { request } from '@umijs/max';
import { getChainConfig } from './config';

// 定义API基础地址 - 动态获取
export const BASE_URL = () => {
  const config = getChainConfig();
  return `https://walletaa.com${config.BASE_URL}`;
  const isDev = process.env.NODE_ENV === 'development';
  return `https://${isDev ? 'dev.' : ''}walletaa.com${config.BASE_URL}`;
};

// 定义交易数据类型
export interface TransactionItem {
  tx_hash: string;
  block_number: number;
  block_hash: string;
  tx_index: number;
  timestamp: number;
  relayer_address: string;
  authorization_fee: number;
  authorization_list: Array<{
    authorizer_address: string;
    code_address: string;
    nonce: number;
    chain_id: number;
  }>;
}

// 定义授权者数据类型
export interface AuthorizerItem {
  authorizer_address: string;
  code_address: string;
  tvl_balance: number;
  set_code_tx_count: number;
  unset_code_tx_count: number;
  historical_code_address: string[];
  last_nonce: number;
  last_chain_id: number;
  provider?: string; // 添加provider字段
}

// 定义代码数据类型
export interface CodeItem {
  code_address: string;
  authorizer_count: number;
  authorization_count: number;
  tvl_balance: number;
  tags?: string[]; // 添加标签字段
  details?: CodeInfoItem; // 添加details字段
  provider?: string; // 添加provider字段
  type?: string; // 添加type字段
}

// 定义中继者数据类型
export interface RelayerItem {
  relayer_address: string;
  tx_count: number;
  authorization_count: number;
  authorization_fee: number;
}

// 定义代码信息详情类型
export interface CodeInfoItem {
  address: string;
  name: string;
  provider: string;
  code: string;
  repo: string;
  contractAccountStandard: string | boolean;
  verificationMethod: string;
  verificationMethodExtra?: string;
  batchCall: string | boolean;
  batchCallExtra?: string;
  executor: string | boolean;
  executorExtra?: string;
  receiveETH: string | boolean;
  receiveNFT: string | boolean;
  recovery: string | boolean;
  recoveryExtra?: string;
  sessionKey: string | boolean;
  sessionKeyExtra?: string;
  storage: string;
  storageExtra?: string;
  nativeETHApprovalAndTransfer: string | boolean;
  nativeETHApprovalAndTransferExtra?: string;
  hooks: string | boolean;
  hooksExtra?: string;
  signature: string;
  signatureExtra?: string;
  txInitiationMethod: string;
  feePaymentMethod: string;
  upgradable: string | boolean;
  upgradableExtra?: string;
  modularContractAccount: string | boolean;
  modularContractAccountExtra?: string;
  moduleRegistry: string | boolean;
  isContractAddress: boolean;
  production: string | boolean;
  audit?: string | boolean;
  auditExtra?: string;
  usage?: string;
  [key: string]: any; // 允许其他可能的属性
}

// 定义TVL数据类型
export interface TVLData {
  total_tvl_balance: number;
  eth_tvl_balance: number;
  weth_tvl_balance: number;
  wbtc_tvl_balance: number;
  usdt_tvl_balance: number;
  usdc_tvl_balance: number;
  dai_tvl_balance: number;
}

// 定义Overview数据类型
export interface Overview {
  tx_count: number;
  authorizer_count: number;
  code_count: number;
  relayer_count: number;
  daily_tx_count: Record<string, number>;
  daily_cumulative_tx_count: Record<string, number>;
  daily_authorizaion_count: Record<string, number>;
  daily_cumulative_authorizaion_count: Record<string, number>;
  daily_code_count: Record<string, number>;
  daily_relayer_count: Record<string, number>;
  top10_codes: Array<{
    code_address: string;
    authorizer_count: number;
    tvl_balance: number;
    provider?: string;
    tags?: string[];
    type?: string;
  }>;
  top10_relayers: Array<{
    relayer_address: string;
    tx_count: number;
    authorization_count: number;
    authorization_fee: number;
  }>;
  top10_authorizers?: Array<{
    authorizer_address: string;
    code_address: string;
    tvl_balance: number;
    provider?: string;
  }>;
  code_infos?: CodeInfoItem[];
  tvls?: TVLData;
}

// 定义Comparison数据类型
export interface ComparisonData {
  [chainName: string]: {
    tx_count: number;
    authorizer_count: number;
    code_count: number;
    relayer_count: number;
    tvls: TVLData;
  };
}

// 定义代码统计数据类型
export interface CodeStatistics {
  code_count_by_type: Record<string, number>;
  code_authorizer_by_type: Record<string, number>;
  code_tvl_by_type: Record<string, number>;
  code_count_by_tag: Record<string, number>;
  code_authorizer_by_tag: Record<string, number>;
  code_tvl_by_tag: Record<string, number>;
}

// 获取交易列表接口
export async function getTransactions(params: {
  page?: number;
  page_size?: number;
  order?: string;
  search_by?: string;
}) {
  return request(`${BASE_URL()}/transactions`, {
    method: 'GET',
    params,
  });
}

// 获取授权者列表接口
export async function getAuthorizers(params: {
  page?: number;
  page_size?: number;
  search_by?: string;
  order?: string;
  order_by?: string;
}) {
  return request(`${BASE_URL()}/authorizers`, {
    method: 'GET',
    params,
  });
}

// 获取包含零代码地址的授权者列表接口
export async function getAuthorizersWithZero(params: {
  page?: number;
  page_size?: number;
  search_by?: string;
  order?: string;
  order_by?: string;
}) {
  return request(`${BASE_URL()}/authorizers_with_zero`, {
    method: 'GET',
    params,
  });
}

// 获取代码列表接口（按ETH余额排序）
export async function getCodesByTvlBalance(params: {
  page?: number;
  page_size?: number;
  order?: string;
  search_by?: string;
  tags_by?: string;
}) {
  return request(`${BASE_URL()}/codes_by_tvl_balance`, {
    method: 'GET',
    params,
  });
}

// 获取代码列表接口（按授权者数量排序）
export async function getCodesByAuthorizerCount(params: {
  page?: number;
  page_size?: number;
  order?: string;
  search_by?: string;
  tags_by?: string;
}) {
  return request(`${BASE_URL()}/codes_by_authorizer_count`, {
    method: 'GET',
    params,
  });
}

// 兼容旧的调用方式
export async function getCodes(params: {
  page?: number;
  page_size?: number;
  order?: string;
}) {
  return getCodesByTvlBalance(params);
}

// 获取中继者列表接口（按交易数量排序）
export async function getRelayersByTxCount(params: {
  page?: number;
  page_size?: number;
  order?: string;
  search_by?: string;
}) {
  return request(`${BASE_URL()}/relayers_by_tx_count`, {
    method: 'GET',
    params,
  });
}

// 获取中继者列表接口（按授权数量排序）
export async function getRelayersByAuthorizationCount(params: {
  page?: number;
  page_size?: number;
  order?: string;
  search_by?: string;
}) {
  return request(`${BASE_URL()}/relayers_by_authorization_count`, {
    method: 'GET',
    params,
  });
}

// 获取中继者列表接口（按授权费用排序）
export async function getRelayersByAuthorizationFee(params: {
  page?: number;
  page_size?: number;
  order?: string;
  search_by?: string;
}) {
  return request(`${BASE_URL()}/relayers_by_authorization_fee`, {
    method: 'GET',
    params,
  });
}

// 获取overview数据
export async function getOverview() {
  return request(`${BASE_URL()}/overview`, {
    method: 'GET',
  });
}

// 获取comparison数据
export async function getComparison(): Promise<ComparisonData> {
  return request(`${BASE_URL()}/comparison`, {
    method: 'GET',
  });
}

// 获取代码统计数据
export async function getCodeStatistics(): Promise<CodeStatistics> {
  return request(`${BASE_URL()}/code_statistics`, {
    method: 'GET',
  });
} 