import { ProColumns, ActionType } from '@ant-design/pro-components';
import {
  PageContainer,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl } from '@umijs/max';
import { Tag, Tooltip } from 'antd';
import React, { useRef, useState } from 'react';
import { getRelayersByTxCount, getRelayersByAuthorizationCount, getRelayersByTxFee, RelayerItem } from '@/services/api';

const Relayers: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [sortApi, setSortApi] = useState<'tx_count' | 'authorization_count' | 'tx_fee'>('tx_count');

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
      valueType: 'digit',
      sorter: true,
      sortDirections: ['ascend', 'descend'],
      defaultSortOrder: sortApi === 'tx_count' ? 'descend' : undefined,
    },
    {
      title: intl.formatMessage({
        id: 'pages.relayers.authorization_count',
        defaultMessage: 'Authorization Count',
      }),
      dataIndex: 'authorization_count',
      valueType: 'digit',
      sorter: true,
      sortDirections: ['ascend', 'descend'],
      defaultSortOrder: sortApi === 'authorization_count' ? 'descend' : undefined,
    },
    {
      title: intl.formatMessage({
        id: 'pages.relayers.tx_fee',
        defaultMessage: 'Transaction Fee (ETH)',
      }),
      dataIndex: 'tx_fee',
      sorter: true,
      sortDirections: ['ascend', 'descend'],
      defaultSortOrder: sortApi === 'tx_fee' ? 'descend' : undefined,
    },
  ];

  // 动态设置表格标题
  const getHeaderTitle = () => {
    if (sortApi === 'tx_count') {
      return intl.formatMessage({
        id: 'pages.relayers.headerTitleTxCount',
        defaultMessage: 'Relayer List (By TX Count)',
      });
    } else if (sortApi === 'authorization_count') {
      return intl.formatMessage({
        id: 'pages.relayers.headerTitleAuthCount',
        defaultMessage: 'Relayer List (By Authorization Count)',
      });
    } else {
      return intl.formatMessage({
        id: 'pages.relayers.headerTitleTxFee',
        defaultMessage: 'Relayer List (By TX Fee)',
      });
    }
  };

  return (
    <PageContainer>
      <ProTable<RelayerItem>
        headerTitle={getHeaderTitle()}
        actionRef={actionRef}
        rowKey="relayer_address"
        search={false}
        request={async (params, sort) => {
          // 将ProTable的params转换为后端API所需的格式
          const { current, pageSize, ...rest } = params;

          // 处理排序参数
          let orderParam = 'desc'; // 默认倒序
          let selectedApi = sortApi;

          if (sort && Object.keys(sort).length > 0) {
            // 获取排序字段和顺序
            const sortField = Object.keys(sort)[0];
            // 修正：在这些API中，正序倒序的逻辑是相反的
            // ProTable的ascend（升序）对应后端的desc（倒序）
            // ProTable的descend（降序）对应后端的asc（正序）
            const sortOrder = sort[sortField] === 'ascend' ? 'desc' : 'asc';
            
            // 根据排序字段选择API
            if (sortField === 'tx_count') {
              selectedApi = 'tx_count';
              setSortApi('tx_count');
            } else if (sortField === 'authorization_count') {
              selectedApi = 'authorization_count';
              setSortApi('authorization_count');
            } else if (sortField === 'tx_fee') {
              selectedApi = 'tx_fee';
              setSortApi('tx_fee');
            }
            
            orderParam = sortOrder;
          }

          // 根据选择的API调用不同的接口
          let msg;
          if (selectedApi === 'tx_count') {
            msg = await getRelayersByTxCount({
              page: current,
              page_size: pageSize,
              order: orderParam,
              ...rest,
            });
          } else if (selectedApi === 'authorization_count') {
            msg = await getRelayersByAuthorizationCount({
              page: current,
              page_size: pageSize,
              order: orderParam,
              ...rest,
            });
          } else {
            msg = await getRelayersByTxFee({
              page: current,
              page_size: pageSize,
              order: orderParam,
              ...rest,
            });
          }

          return {
            data: msg.relayers || [],
            success: true,
            total: msg.total || 0,
          };
        }}
        columns={columns}
      />
    </PageContainer>
  );
};

export default Relayers; 