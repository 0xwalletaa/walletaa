import { request } from '@umijs/max';
import { getChainConfig } from './config';

// 定义API基础地址 - 动态获取
export const BASE_URL = () => {
  const config = getChainConfig();
  return `https://walletaa.com${config.BASE_URL}`;
};

// 定义交易数据类型
export interface TransactionItem {
  tx_hash: string;
  block_number: number;
  block_hash: string;
  tx_index: number;
  timestamp: number;
  relayer_address: string;
  tx_fee: number;
  authorization_list: Array<{
    authorizer_address: string;
    code_address: string;
  }>;
}

// 定义授权者数据类型
export interface AuthorizerItem {
  authorizer_address: string;
  code_address: string;
  eth_balance: number;
  set_code_tx_count: number;
  unset_code_tx_count: number;
  historical_code_address: string[];
}

// 定义代码数据类型
export interface CodeItem {
  code_address: string;
  authorizer_count: number;
  authorization_count: number;
  eth_balance: number;
}

// 定义中继者数据类型
export interface RelayerItem {
  relayer_address: string;
  tx_count: number;
  authorization_count: number;
  tx_fee: number;
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
  batchCall: string | boolean;
  executor: string | boolean;
  receiveETH: string | boolean;
  receiveNFT: string | boolean;
  recovery: string | boolean;
  sessionKey: string | boolean;
  storage: string;
  nativeETHApprovalAndTransfer: string | boolean;
  hooks: string | boolean;
  signature: string;
  txInitiationMethod: string;
  feePaymentMethod: string;
  upgradable: string | boolean;
  modularContractAccount: string | boolean;
  moduleRegistry: string | boolean;
  isContractAddress: boolean;
  production: string | boolean;
  [key: string]: any; // 允许其他可能的属性
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
    eth_balance: number;
  }>;
  top10_relayers: Array<{
    relayer_address: string;
    tx_count: number;
    authorization_count: number;
    tx_fee: number;
  }>;
}

// 获取交易列表接口
export async function getTransactions(params: {
  page?: number;
  page_size?: number;
  order?: string;
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
}) {
  return request(`${BASE_URL()}/authorizers_with_zero`, {
    method: 'GET',
    params,
  });
}

// 获取代码列表接口（按ETH余额排序）
export async function getCodesByEthBalance(params: {
  page?: number;
  page_size?: number;
  order?: string;
}) {
  return request(`${BASE_URL()}/codes_by_eth_balance`, {
    method: 'GET',
    params,
  });
}

// 获取代码列表接口（按授权者数量排序）
export async function getCodesByAuthorizerCount(params: {
  page?: number;
  page_size?: number;
  order?: string;
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
  return getCodesByEthBalance(params);
}

// 获取中继者列表接口（按交易数量排序）
export async function getRelayersByTxCount(params: {
  page?: number;
  page_size?: number;
  order?: string;
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
}) {
  return request(`${BASE_URL()}/relayers_by_authorization_count`, {
    method: 'GET',
    params,
  });
}

// 获取中继者列表接口（按交易费用排序）
export async function getRelayersByTxFee(params: {
  page?: number;
  page_size?: number;
  order?: string;
}) {
  return request(`${BASE_URL()}/relayers_by_tx_fee`, {
    method: 'GET',
    params,
  });
}

// 获取完整的code_infos数据
export async function getCodeInfos() {
  return request(`${BASE_URL()}/code_infos`, {
    method: 'GET',
  });
}

// 获取overview数据
export async function getOverview() {
  return request(`${BASE_URL()}/overview`, {
    method: 'GET',
  });
} 