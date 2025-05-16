import { ProColumns, ActionType } from '@ant-design/pro-components';
import {
  PageContainer,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl } from '@umijs/max';
import { Tag, Tooltip, Switch, Space } from 'antd';
import { LinkOutlined } from '@ant-design/icons';
import React, { useRef, useState } from 'react';
import { getAuthorizers, getAuthorizersWithZero, AuthorizerItem } from '@/services/api';
import { getChainConfig } from '@/services/config';

const Authorizers: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [includeZero, setIncludeZero] = useState<boolean>(false);
  const { EXPLORER_URL } = getChainConfig();

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
      render: (dom, record) => {
        return typeof dom === 'string' && dom.length > 10
          ? (
            <div>
              <Tooltip title={
                <span>
                  {dom}
                  <a href={`${EXPLORER_URL}/address/${dom}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                    <LinkOutlined />
                  </a>
                </span>
              }>
                <Tag color="blue">{`${formatAddress(dom as string)}`}</Tag>
              </Tooltip>
              {record.last_nonce === 0 && (
                <Tooltip title={
                  <span>
                    {intl.formatMessage({
                      id: 'pages.authorizers.newEOA',
                      defaultMessage: 'New Account with last_nonce=0',
                    })}
                  </span>
                }>
                  <Tag color="red">
                    {intl.formatMessage({
                      id: 'pages.authorizers.newEOATag',
                      defaultMessage: 'NewEOA',
                    })}
                  </Tag>
                </Tooltip>
              )}
              {record.last_chain_id === 0 && (
                <Tooltip title={
                  <span>
                    {intl.formatMessage({
                      id: 'pages.authorizers.crossAuth',
                      defaultMessage: 'Cross-chain Authentication with last_chain_id=0',
                    })}
                  </span>
                }>
                  <Tag color="red">
                    {intl.formatMessage({
                      id: 'pages.authorizers.crossAuthTag',
                      defaultMessage: 'CrossAuth',
                    })}
                  </Tag>
                </Tooltip>
              )}
            </div>
          )
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
          ? <Tooltip title={
              <span>
                {dom}
                <a href={`${EXPLORER_URL}/address/${dom}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                  <LinkOutlined />
                </a>
              </span>
            }>
              <Tag color="green">{`${formatAddress(dom as string)}`}</Tag>
            </Tooltip>
          : <Tag color="green">{dom}</Tag>;
      },
    },
    {
      title: intl.formatMessage({
        id: 'pages.authorizers.set_code_tx_count',
        defaultMessage: 'Set Code Count',
      }),
      dataIndex: 'set_code_tx_count',
      valueType: 'digit',
    },
    {
      title: intl.formatMessage({
        id: 'pages.authorizers.unset_code_tx_count',
        defaultMessage: 'Unset Code Count',
      }),
      dataIndex: 'unset_code_tx_count',
      valueType: 'digit',
    },
    {
      title: intl.formatMessage({
        id: 'pages.authorizers.eth_balance',
        defaultMessage: 'ETH Balance',
      }),
      dataIndex: 'eth_balance',
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
              <Tooltip key={index} title={
                <span>
                  {address}
                  <a href={`${EXPLORER_URL}/address/${address}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                    <LinkOutlined />
                  </a>
                </span>
              }>
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
        toolBarRender={() => [
          <Space key="switch">
            <Switch 
              checked={includeZero} 
              onChange={(checked) => {
                setIncludeZero(checked);
                if (actionRef.current) {
                  actionRef.current.reload();
                }
              }} 
            />
            <span style={{ fontWeight: 300 }}>{intl.formatMessage({
              id: 'pages.authorizers.includeZero',
              defaultMessage: 'Include Canceled',
            })}</span>
          </Space>
        ]}
        actionRef={actionRef}
        rowKey="authorizer_address"
        search={false}
        request={async (params) => {
          // 将ProTable的params转换为后端API所需的格式
          const { current, pageSize, ...rest } = params;
          
          // 根据开关状态选择API
          const fetchFunction = includeZero ? getAuthorizersWithZero : getAuthorizers;
          
          const msg = await fetchFunction({
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