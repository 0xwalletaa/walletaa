import { PlusOutlined, ArrowRightOutlined } from '@ant-design/icons';
import type { ActionType, ProColumns, ProDescriptionsItemProps } from '@ant-design/pro-components';
import {
  PageContainer,
  ProDescriptions,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl } from '@umijs/max';
import { Drawer, Tag, Tooltip } from 'antd';
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

  const formatAddress = (address: string) => {
    return typeof address === 'string' && address.length > 10
      ? `${address.substring(0, 6)}...${address.substring(address.length - 4)}`
      : address;
  };

  const columns: ProColumns<TransactionItem>[] = [
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
        id: 'pages.transactions.tx_hash',
        defaultMessage: 'Transaction Hash',
      }),
      dataIndex: 'tx_hash',
      render: (dom, entity) => {
        return (
          <span>
            {formatAddress(dom as string)}
          </span>
        );
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
          ? <Tooltip title={dom}><Tag color="purple">{`${dom.substring(0, 6)}...${dom.substring(dom.length - 4)}`}</Tag></Tooltip>
          : <Tag color="purple">{dom}</Tag>;
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
      render: (_, record) => {
        if (!record.authorization_list || record.authorization_list.length === 0) {
          return (
            <span>
              {intl.formatMessage({
                id: 'pages.transactions.noAuthorizationData',
                defaultMessage: 'No Authorization Data',
              })}
            </span>
          );
        }
        
        if (record.authorization_list.length <= 3) {
          return (
            <div>
              {record.authorization_list.map((auth, index) => (
                <div key={index} style={{ marginBottom: 4 }}>
                  <Tooltip title={auth.authorizer_address}>
                    <Tag color="blue">{formatAddress(auth.authorizer_address)}</Tag>
                  </Tooltip>
                  <Tooltip title={auth.code_address}>
                    <Tag color="green">{formatAddress(auth.code_address)}</Tag>
                  </Tooltip>
                </div>
              ))}
            </div>
          );
        } else {
          return (
            <a
              onClick={() => {
                setCurrentRow(record);
                setShowDetail(true);
              }}
            >
              {intl.formatMessage(
                { id: 'pages.transactions.viewMore', defaultMessage: 'View all {count} authorizations' },
                { count: record.authorization_list.length }
              )}
            </a>
          );
        }
      },
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
            <h2>{intl.formatMessage({
              id: 'pages.transactions.authorizationList',
              defaultMessage: 'Authorization List',
            })}</h2>
            <p>{intl.formatMessage({
              id: 'pages.transactions.transactionHash',
              defaultMessage: 'Transaction Hash',
            })}: {currentRow.tx_hash}</p>
            
            <div style={{ marginTop: 20 }}>
              {currentRow.authorization_list && currentRow.authorization_list.length > 0 ? (
                <ul style={{ padding: 0, listStyle: 'none' }}>
                  {currentRow.authorization_list.map((auth, index) => (
                    <li key={index} style={{ marginBottom: 12, padding: 10, border: '1px solid #f0f0f0', borderRadius: 4 }}>
                      <div><strong>{intl.formatMessage({
                        id: 'pages.transactions.authorizerAddress',
                        defaultMessage: 'Authorizer Address',
                      })}:</strong> <Tooltip title={auth.authorizer_address}><Tag color="blue">{auth.authorizer_address}</Tag></Tooltip></div>
                      <div><strong>{intl.formatMessage({
                        id: 'pages.transactions.codeAddress',
                        defaultMessage: 'Code Address',
                      })}:</strong> <Tooltip title={auth.code_address}><Tag color="green">{auth.code_address}</Tag></Tooltip></div>
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
