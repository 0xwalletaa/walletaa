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

const Transactions: React.FC = () => {
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
      title: intl.formatMessage({
        id: 'pages.transactions.tx_hash',
        defaultMessage: 'Transaction Hash',
      }),
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
      title: intl.formatMessage({
        id: 'pages.transactions.block_number',
        defaultMessage: 'Block Number',
      }),
      dataIndex: 'block_number',
      sorter: true,
    },
    {
      title: intl.formatMessage({
        id: 'pages.transactions.timestamp',
        defaultMessage: 'Timestamp',
      }),
      dataIndex: 'timestamp',
      valueType: 'dateTime',
      sorter: true,
      renderText: (val: number) => {
        // 将秒级时间戳转换为毫秒级时间戳（如果时间戳是秒级的）
        return val * 1000;
      },
    },
    {
      title: intl.formatMessage({
        id: 'pages.transactions.relayer_address',
        defaultMessage: 'Relayer Address',
      }),
      dataIndex: 'relayer_address',
      render: (dom) => {
        return typeof dom === 'string' && dom.length > 10
          ? `${dom.substring(0, 6)}...${dom.substring(dom.length - 4)}`
          : dom;
      },
    },
    {
      title: intl.formatMessage({
        id: 'pages.transactions.tx_index',
        defaultMessage: 'Transaction Index',
      }),
      dataIndex: 'tx_index',
      valueType: 'digit',
    },
    {
      title: intl.formatMessage({
        id: 'pages.transactions.tx_fee',
        defaultMessage: 'Transaction Fee (ETH)',
      }),
      dataIndex: 'tx_fee',
      sorter: true,
    },
    {
      title: intl.formatMessage({
        id: 'pages.transactions.authorization_list',
        defaultMessage: 'Authorization List',
      }),
      dataIndex: 'authorization_list',
      render: (_, record) => record.authorization_list?.length || 0,
    },
  ];

  return (
    <PageContainer>
      <ProTable<TransactionItem>
        headerTitle={intl.formatMessage({
          id: 'pages.transactions.headerTitle',
          defaultMessage: 'Transaction List',
        })}
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
              title={intl.formatMessage({
                id: 'pages.transactions.detailTitle',
                defaultMessage: 'Transaction Details',
              })}
              request={async () => ({
                data: currentRow || {},
              })}
              params={{
                id: currentRow?.tx_hash,
              }}
              columns={columns as ProDescriptionsItemProps<TransactionItem>[]}
            />
            
            <div style={{ marginTop: 20 }}>
              <h3>{intl.formatMessage({
                id: 'pages.transactions.authorizationList',
                defaultMessage: 'Authorization List',
              })}</h3>
              {currentRow.authorization_list && currentRow.authorization_list.length > 0 ? (
                <ul>
                  {currentRow.authorization_list.map((auth, index) => (
                    <li key={index}>
                      <strong>{intl.formatMessage({
                        id: 'pages.transactions.authorizerAddress',
                        defaultMessage: 'Authorizer Address',
                      })}:</strong> {auth.authorizer_address.substring(0, 6)}...{auth.authorizer_address.substring(auth.authorizer_address.length - 4)}
                      <div><strong>{intl.formatMessage({
                        id: 'pages.transactions.codeAddress',
                        defaultMessage: 'Code Address',
                      })}:</strong> {auth.code_address.substring(0, 6)}...{auth.code_address.substring(auth.code_address.length - 4)}</div>
                    </li>
                  ))}
                </ul>
              ) : (
                <p>{intl.formatMessage({
                  id: 'pages.transactions.noAuthorizationData',
                  defaultMessage: 'No Authorization Data',
                })}</p>
              )}
            </div>
          </>
        )}
      </Drawer>
    </PageContainer>
  );
};

export default Transactions;
