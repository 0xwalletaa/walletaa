import { ProColumns, ActionType } from '@ant-design/pro-components';
import {
  PageContainer,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl, history, useLocation } from '@umijs/max';
import { Tag, Tooltip, Button, Card, Row, Col, Input } from 'antd';
import { LinkOutlined, SearchOutlined } from '@ant-design/icons';
import React, { useRef, useState, useEffect } from 'react';
import { getRelayersByTxCount, getRelayersByAuthorizationCount, getRelayersByAuthorizationFee, RelayerItem } from '@/services/api';
import { getChainConfig } from '@/services/config';
import numeral from 'numeral';

const Relayers: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [sortApi, setSortApi] = useState<'tx_count' | 'authorization_count' | 'authorization_fee'>('tx_count');
  const [searchValue, setSearchValue] = useState<string>('');
  const [searchByParam, setSearchByParam] = useState<string>('');
  const { EXPLORER_URL } = getChainConfig();
  const location = useLocation();

  /**
   * @en-US International configuration
   * @zh-CN 国际化配置
   * */
  const intl = useIntl();

  // 从URL参数中获取search_by
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const searchBy = params.get('search_by');
    if (searchBy) {
      setSearchValue(searchBy);
      setSearchByParam(searchBy);
    }
  }, [location.search]);

  // 处理搜索操作
  const handleSearch = () => {
    setSearchByParam(searchValue);
    
    // 更新URL参数
    const params = new URLSearchParams(location.search);
    if (searchValue) {
      params.set('search_by', searchValue);
    } else {
      params.delete('search_by');
    }
    
    // 构建新的URL
    const newSearch = params.toString();
    const pathname = location.pathname;
    const newPath = newSearch ? `${pathname}?${newSearch}` : pathname;
    
    // 使用history更新URL，不刷新页面
    history.push(newPath);
    
    // 重新加载表格数据并重置到第一页
    if (actionRef.current) {
      actionRef.current.reload(true);
    }
  };

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
          ? <Tooltip title={
              <span>
                {dom}
                <a href={`${EXPLORER_URL}/address/${dom}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                  <LinkOutlined />
                </a>
              </span>
            }>
              <Tag color="purple">{`${formatAddress(dom as string)}`}</Tag>
            </Tooltip>
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
      sortDirections: ['descend', 'ascend'],
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
      sortDirections: ['descend', 'ascend'],
      defaultSortOrder: sortApi === 'authorization_count' ? 'descend' : undefined,
    },
    {
      title: intl.formatMessage({
        id: 'pages.relayers.authorization_fee',
        defaultMessage: 'Authorization Fee (ETH)',
      }),
      dataIndex: 'authorization_fee',
      sorter: true,
      sortDirections: ['descend', 'ascend'],
      defaultSortOrder: sortApi === 'authorization_fee' ? 'descend' : undefined,
      render: (dom: any) => {
        if (typeof dom === 'number') {
          // 对于极小的数字（小于0.01），使用科学计数法显示
          if (Math.abs(dom) < 0.01 && dom !== 0) {
            return dom.toExponential(2);
          }
          // 对于正常范围的数字，使用千分位格式
          return numeral(dom).format('0,0.00');
        }
        return dom;
      },
    },
  ];

  // 动态设置表格标题
  const getHeaderTitle = () => {
    return intl.formatMessage({
      id: 'pages.relayers.headerTitle',
      defaultMessage: 'Relayer List',
    });
  };

  return (
    <PageContainer>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col flex="auto">
            <Input
              placeholder={intl.formatMessage({
                id: 'pages.relayers.search.placeholder',
                defaultMessage: '输入中继器地址',
              })}
              value={searchValue}
              onChange={(e) => setSearchValue(e.target.value)}
              onPressEnter={handleSearch}
            />
          </Col>
          <Col>
            <Button 
              type="primary" 
              icon={<SearchOutlined />} 
              onClick={handleSearch}
            >
              {intl.formatMessage({
                id: 'pages.relayers.search.button',
                defaultMessage: '搜索',
              })}
            </Button>
          </Col>
        </Row>
      </Card>
      
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
            const sortOrder = sort[sortField] === 'ascend' ? 'asc' : 'desc';
            
            // 根据排序字段选择API
            if (sortField === 'tx_count') {
              selectedApi = 'tx_count';
              setSortApi('tx_count');
            } else if (sortField === 'authorization_count') {
              selectedApi = 'authorization_count';
              setSortApi('authorization_count');
            } else if (sortField === 'authorization_fee') {
              selectedApi = 'authorization_fee';
              setSortApi('authorization_fee');
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
              search_by: searchByParam.toLowerCase(),
              ...rest,
            });
          } else if (selectedApi === 'authorization_count') {
            msg = await getRelayersByAuthorizationCount({
              page: current,
              page_size: pageSize,
              order: orderParam,
              search_by: searchByParam.toLowerCase(),
              ...rest,
            });
          } else {
            msg = await getRelayersByAuthorizationFee({
              page: current,
              page_size: pageSize,
              order: orderParam,
              search_by: searchByParam.toLowerCase(),
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