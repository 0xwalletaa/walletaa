import { PlusOutlined } from '@ant-design/icons';
import type { ActionType, ProColumns, ProDescriptionsItemProps } from '@ant-design/pro-components';
import {
  PageContainer,
  ProDescriptions,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl } from '@umijs/max';
import { Drawer, Tag } from 'antd';
import React, { useRef, useState } from 'react';
import { getTransactions, TransactionItem } from '@/services/api';

const TableList: React.FC = () => {
  const [showDetail, setShowDetail] = useState<boolean>(false);
  const actionRef = useRef<ActionType>();
  const [currentRow, setCurrentRow] = useState<TransactionItem>();

  /**
   * @en-US International configuration
   * @zh-CN 国际化配置
   * */
  const intl = useIntl();

  const columns: ProColumns<TransactionItem>[] = [
    {
      title: '交易哈希',
      dataIndex: 'tx_hash',
      render: (dom, entity) => {
        return (
          <a
            onClick={() => {
              setCurrentRow(entity);
              setShowDetail(true);
            }}
          >
            {typeof dom === 'string' && dom.length > 10
              ? `${dom.substring(0, 6)}...${dom.substring(dom.length - 4)}`
              : dom}
          </a>
        );
      },
    },
    {
      title: '区块',
      dataIndex: 'block_number',
      sorter: true,
    },
    {
      title: '时间戳',
      dataIndex: 'timestamp',
      valueType: 'dateTime',
      sorter: true,
    },
    {
      title: '中继者地址',
      dataIndex: 'relayer_address',
      render: (dom) => {
        return typeof dom === 'string' && dom.length > 10
          ? `${dom.substring(0, 6)}...${dom.substring(dom.length - 4)}`
          : dom;
      },
    },
    {
      title: '交易索引',
      dataIndex: 'tx_index',
      valueType: 'digit',
    },
    {
      title: '交易费用 (ETH)',
      dataIndex: 'tx_fee',
      valueType: 'money',
      sorter: true,
    },
    {
      title: '授权者数量',
      dataIndex: 'authorization_list',
      render: (_, record) => record.authorization_list?.length || 0,
    },
  ];

  return (
    <PageContainer>
      <ProTable<TransactionItem>
        headerTitle="交易列表"
        actionRef={actionRef}
        rowKey="tx_hash"
        search={false}
        request={async (params) => {
          // 将ProTable的params转换为后端API所需的格式
          const { current, pageSize, ...rest } = params;
          const msg = await getTransactions({
            page: current,
            page_size: pageSize,
            ...rest,
          });
          return {
            data: msg.transactions || [],
            success: true,
            total: msg.total || 0,
          };
        }}
        columns={columns}
        pagination={{
          pageSize: 10,
        }}
      />

      <Drawer
        width={600}
        open={showDetail}
        onClose={() => {
          setCurrentRow(undefined);
          setShowDetail(false);
        }}
        closable={false}
      >
        {currentRow?.tx_hash && (
          <>
            <ProDescriptions<TransactionItem>
              column={2}
              title={`交易详情: ${currentRow.tx_hash.substring(0, 6)}...${currentRow.tx_hash.substring(currentRow.tx_hash.length - 4)}`}
              request={async () => ({
                data: currentRow || {},
              })}
              params={{
                id: currentRow?.tx_hash,
              }}
              columns={columns as ProDescriptionsItemProps<TransactionItem>[]}
            />
            
            <div style={{ marginTop: 20 }}>
              <h3>授权列表</h3>
              {currentRow.authorization_list && currentRow.authorization_list.length > 0 ? (
                <ul>
                  {currentRow.authorization_list.map((auth, index) => (
                    <li key={index}>
                      <strong>授权者地址:</strong> {auth.authorizer_address.substring(0, 6)}...{auth.authorizer_address.substring(auth.authorizer_address.length - 4)}
                      <div><strong>代码地址:</strong> {auth.code_address.substring(0, 6)}...{auth.code_address.substring(auth.code_address.length - 4)}</div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p>无授权数据</p>
              )}
            </div>
          </>
        )}
      </Drawer>
    </PageContainer>
  );
};

export default TableList;
