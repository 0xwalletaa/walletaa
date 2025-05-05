import { ProColumns, ActionType } from '@ant-design/pro-components';
import {
  PageContainer,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl } from '@umijs/max';
import { Tag, Tooltip } from 'antd';
import React, { useRef } from 'react';
import { getRelayers, RelayerItem } from '@/services/api';

const Relayers: React.FC = () => {
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

  const columns: ProColumns<RelayerItem>[] = [
    {
      title: intl.formatMessage({
        id: 'pages.relayers.relayer_address',
        defaultMessage: 'Relayer Address',
      }),
      dataIndex: 'relayer_address',
      render: (dom) => {
        return typeof dom === 'string' && dom.length > 10
          ? <Tooltip title={dom}><Tag color="purple">{`${formatAddress(dom as string)}`}</Tag></Tooltip>
          : <Tag color="purple">{dom}</Tag>;
      },
    },
    {
      title: intl.formatMessage({
        id: 'pages.relayers.tx_count',
        defaultMessage: 'Transaction Count',
      }),
      dataIndex: 'tx_count',
      sorter: true,
      valueType: 'digit',
    },
    {
      title: intl.formatMessage({
        id: 'pages.relayers.authorization_count',
        defaultMessage: 'Authorization Count',
      }),
      dataIndex: 'authorization_count',
      sorter: true,
      valueType: 'digit',
    },
    {
      title: intl.formatMessage({
        id: 'pages.relayers.tx_fee',
        defaultMessage: 'Transaction Fee (ETH)',
      }),
      dataIndex: 'tx_fee',
      sorter: true,
    },
  ];

  return (
    <PageContainer>
      <ProTable<RelayerItem>
        headerTitle={intl.formatMessage({
          id: 'pages.relayers.headerTitle',
          defaultMessage: 'Relayer List (By TX Count)',
        })}
        actionRef={actionRef}
        rowKey="relayer_address"
        search={false}
        request={async (params) => {
          // 将ProTable的params转换为后端API所需的格式
          const { current, pageSize, ...rest } = params;
          const msg = await getRelayers({
            page: current,
            page_size: pageSize,
            ...rest,
          });
          return {
            data: msg.relayers || [],
            success: true,
            total: msg.total || 0,
          };
        }}
        columns={columns}
        pagination={{
          pageSize: 10,
        }}
      />
    </PageContainer>
  );
};

export default Relayers; 