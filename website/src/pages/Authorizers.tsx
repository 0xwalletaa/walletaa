import { ProColumns, ActionType } from '@ant-design/pro-components';
import {
  PageContainer,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl } from '@umijs/max';
import { Tag, Tooltip } from 'antd';
import React, { useRef } from 'react';
import { getAuthorizers, AuthorizerItem } from '@/services/api';

const Authorizers: React.FC = () => {
  const actionRef = useRef<ActionType>();

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

  const columns: ProColumns<AuthorizerItem>[] = [
    {
      title: intl.formatMessage({
        id: 'pages.authorizers.authorizer_address',
        defaultMessage: 'Authorizer Address',
      }),
      dataIndex: 'authorizer_address',
      render: (dom) => {
        return typeof dom === 'string' && dom.length > 10
          ? <Tooltip title={dom}><Tag color="blue">{`${formatAddress(dom as string)}`}</Tag></Tooltip>
          : <Tag color="blue">{dom}</Tag>;
      },
    },
    {
      title: intl.formatMessage({
        id: 'pages.authorizers.code_address',
        defaultMessage: 'Code Address',
      }),
      dataIndex: 'code_address',
      render: (dom) => {
        return typeof dom === 'string' && dom.length > 10
          ? <Tooltip title={dom}><Tag color="green">{`${formatAddress(dom as string)}`}</Tag></Tooltip>
          : <Tag color="green">{dom}</Tag>;
      },
    },
    {
      title: intl.formatMessage({
        id: 'pages.authorizers.set_code_tx_count',
        defaultMessage: 'Set Code Count',
      }),
      dataIndex: 'set_code_tx_count',
      sorter: true,
      valueType: 'digit',
    },
    {
      title: intl.formatMessage({
        id: 'pages.authorizers.unset_code_tx_count',
        defaultMessage: 'Unset Code Count',
      }),
      dataIndex: 'unset_code_tx_count',
      sorter: true,
      valueType: 'digit',
    },
    {
      title: intl.formatMessage({
        id: 'pages.authorizers.eth_balance',
        defaultMessage: 'ETH Balance',
      }),
      dataIndex: 'eth_balance',
      sorter: true,
    },
    {
      title: intl.formatMessage({
        id: 'pages.authorizers.historical_code_address',
        defaultMessage: 'Historical Code Address',
      }),
      dataIndex: 'historical_code_address',
      render: (dom) => {
        if (!dom || !Array.isArray(dom) || dom.length === 0) {
          return '-';
        }
        return (
          <div>
            {(dom as string[]).map((address, index) => (
              <Tooltip key={index} title={address}>
                <Tag color="purple" style={{ marginBottom: '2px' }}>{`${formatAddress(address)}`}</Tag>
              </Tooltip>
            ))}
          </div>
        );
      },
    },
  ];

  return (
    <PageContainer>
      <ProTable<AuthorizerItem>
        headerTitle={intl.formatMessage({
          id: 'pages.authorizers.headerTitle',
          defaultMessage: 'Authorizer List',
        })}
        actionRef={actionRef}
        rowKey="authorizer_address"
        search={false}
        request={async (params) => {
          // 将ProTable的params转换为后端API所需的格式
          const { current, pageSize, ...rest } = params;
          const msg = await getAuthorizers({
            page: current,
            page_size: pageSize,
            ...rest,
          });
          return {
            data: msg.authorizers || [],
            success: true,
            total: msg.total || 0,
          };
        }}
        columns={columns}
      />
    </PageContainer>
  );
};

export default Authorizers; 