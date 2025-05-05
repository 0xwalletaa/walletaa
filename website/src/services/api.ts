import { request } from '@umijs/max';

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

// 获取交易列表接口
export async function getTransactions(params: {
  page?: number;
  page_size?: number;
}) {
  return request('http://47.242.237.111:8082/transactions', {
    method: 'GET',
    params,
  });
}

// 获取授权者列表接口
export async function getAuthorizers(params: {
  page?: number;
  page_size?: number;
}) {
  return request('http://47.242.237.111:8082/authorizers', {
    method: 'GET',
    params,
  });
}

// 获取代码列表接口（按ETH余额排序）
export async function getCodes(params: {
  page?: number;
  page_size?: number;
}) {
  return request('http://47.242.237.111:8082/codes_by_eth_balance', {
    method: 'GET',
    params,
  });
}

// 获取中继者列表接口（按交易数量排序）
export async function getRelayers(params: {
  page?: number;
  page_size?: number;
}) {
  return request('http://47.242.237.111:8082/relayers_by_tx_count', {
    method: 'GET',
    params,
  });
} 