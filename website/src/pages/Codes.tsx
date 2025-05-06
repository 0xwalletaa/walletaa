import { ProColumns, ActionType } from '@ant-design/pro-components';
import {
  PageContainer,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl } from '@umijs/max';
import { Tag, Tooltip } from 'antd';
import React, { useRef, useState } from 'react';
import { getCodesByEthBalance, getCodesByAuthorizerCount, CodeItem } from '@/services/api';

const Codes: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [sortApi, setSortApi] = useState<'eth_balance' | 'authorizer_count'>('eth_balance');

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

  const columns: ProColumns<CodeItem>[] = [
    {
      title: intl.formatMessage({
        id: 'pages.codes.code_address',
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
        id: 'pages.codes.authorizer_count',
        defaultMessage: 'Authorizer Count',
      }),
      dataIndex: 'authorizer_count',
      valueType: 'digit',
      sorter: true,
      sortDirections: ['ascend', 'descend'],
      defaultSortOrder: sortApi === 'authorizer_count' ? 'descend' : undefined,
    },
    {
      title: intl.formatMessage({
        id: 'pages.codes.eth_balance',
        defaultMessage: 'ETH Balance',
      }),
      dataIndex: 'eth_balance',
      sorter: true,
      sortDirections: ['ascend', 'descend'],
      defaultSortOrder: sortApi === 'eth_balance' ? 'descend' : undefined,
    },
  ];

  // 动态设置表格标题
  const getHeaderTitle = () => {
    if (sortApi === 'eth_balance') {
      return intl.formatMessage({
        id: 'pages.codes.headerTitleEthBalance',
        defaultMessage: 'Code List (By ETH Balance)',
      });
    } else {
      return intl.formatMessage({
        id: 'pages.codes.headerTitleAuthorizerCount',
        defaultMessage: 'Code List (By Authorizer Count)',
      });
    }
  };

  return (
    <PageContainer>
      <ProTable<CodeItem>
        headerTitle={getHeaderTitle()}
        actionRef={actionRef}
        rowKey="code_address"
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
            const sortOrder = sort[sortField] === 'ascend' ? 'desc' : 'asc';
            
            // 根据排序字段选择API
            if (sortField === 'eth_balance') {
              selectedApi = 'eth_balance';
              setSortApi('eth_balance');
            } else if (sortField === 'authorizer_count') {
              selectedApi = 'authorizer_count';
              setSortApi('authorizer_count');
            }
            
            orderParam = sortOrder;
          }

          // 根据选择的API调用不同的接口
          let msg;
          if (selectedApi === 'eth_balance') {
            msg = await getCodesByEthBalance({
              page: current,
              page_size: pageSize,
              order: orderParam,
              ...rest,
            });
          } else {
            msg = await getCodesByAuthorizerCount({
              page: current,
              page_size: pageSize,
              order: orderParam,
              ...rest,
            });
          }

          return {
            data: msg.codes || [],
            success: true,
            total: msg.total || 0,
          };
        }}
        columns={columns}
      />
    </PageContainer>
  );
};

export default Codes; 