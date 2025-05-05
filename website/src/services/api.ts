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