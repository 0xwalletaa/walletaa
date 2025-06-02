import { ProColumns, ActionType } from '@ant-design/pro-components';
import {
  PageContainer,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl, history, useLocation } from '@umijs/max';
import { Tag, Tooltip, Switch, Space, Input, Button, Card, Row, Col, Modal } from 'antd';
import { LinkOutlined, SearchOutlined, InfoCircleOutlined } from '@ant-design/icons';
import React, { useRef, useState, useEffect } from 'react';
import { getAuthorizers, getAuthorizersWithZero, AuthorizerItem } from '@/services/api';
import { getChainConfig } from '@/services/config';
import numeral from 'numeral';

const Authorizers: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [includeZero, setIncludeZero] = useState<boolean>(false);
  const [sortApi, setSortApi] = useState<'tvl_balance' | 'historical_code_address_count'>('tvl_balance');
  const [searchValue, setSearchValue] = useState<string>('');
  const [searchByParam, setSearchByParam] = useState<string>('');
  const [showDetail, setShowDetail] = useState<boolean>(false);
  const [currentRow, setCurrentRow] = useState<AuthorizerItem>();
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
        id: 'pages.authorizers.provider',
        defaultMessage: 'Provider',
      }),
      dataIndex: 'provider',
      render: (dom, record) => {
        return record.provider ? (
          <Tag color="volcano">{record.provider}</Tag>
        ) : null;
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
      title: (
        <Space>
          {intl.formatMessage({
            id: 'pages.authorizers.tvl_balance',
            defaultMessage: 'TVL',
          })}
          <Tooltip title="TVL = ETH + WETH + WBTC + USDT + USDC + DAI">
            <InfoCircleOutlined style={{ color: 'rgba(0,0,0,.45)' }} />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'tvl_balance',
      align: 'right',
      sorter: true,
      sortDirections: ['descend', 'ascend'],
      defaultSortOrder: sortApi === 'tvl_balance' ? 'descend' : undefined,
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
    {
      title: intl.formatMessage({
        id: 'pages.authorizers.historical_code_address',
        defaultMessage: 'Historical Code Address',
      }),
      dataIndex: 'historical_code_address',
      sorter: true,
      sortDirections: ['descend', 'ascend'],
      defaultSortOrder: sortApi === 'historical_code_address_count' ? 'descend' : undefined,
      render: (dom) => {
        if (!dom || !Array.isArray(dom) || dom.length === 0) {
          return '-';
        }
        
        if (dom.length <= 10) {
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
        } else {
          return (
            <a
              onClick={() => {
                setCurrentRow({ ...currentRow, historical_code_address: dom } as AuthorizerItem);
                setShowDetail(true);
              }}
            >
              {intl.formatMessage(
                { id: 'pages.authorizers.viewMore', defaultMessage: '查看全部 {count} 个历史代码地址' },
                { count: dom.length }
              )}
            </a>
          );
        }
      },
    },
  ];

  return (
    <PageContainer>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col flex="auto">
            <Input
              placeholder={intl.formatMessage({
                id: 'pages.authorizers.search.placeholder',
                defaultMessage: '输入授权者地址或代码地址',
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
                id: 'pages.authorizers.search.button',
                defaultMessage: '搜索',
              })}
            </Button>
          </Col>
        </Row>
      </Card>
      
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
        request={async (params, sort) => {
          // 将ProTable的params转换为后端API所需的格式
          const { current, pageSize, ...rest } = params;

          // 处理排序参数
          let orderParam = 'desc'; // 默认倒序
          let orderByParam = sortApi; // 默认使用当前sortApi

          if (sort && Object.keys(sort).length > 0) {
            // 获取排序字段和顺序
            const sortField = Object.keys(sort)[0];
            const sortOrder = sort[sortField] === 'ascend' ? 'asc' : 'desc';
            
            // 根据排序字段选择order_by参数
            if (sortField === 'tvl_balance') {
              orderByParam = 'tvl_balance';
              setSortApi('tvl_balance');
            } else if (sortField === 'historical_code_address') {
              orderByParam = 'historical_code_address_count';
              setSortApi('historical_code_address_count');
            }
            
            orderParam = sortOrder;
          }
          
          // 根据开关状态选择API
          const fetchFunction = includeZero ? getAuthorizersWithZero : getAuthorizers;
          
          const msg = await fetchFunction({
            page: current,
            page_size: pageSize,
            search_by: searchByParam.toLowerCase(),
            order: orderParam,
            order_by: orderByParam,
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

      <Modal
        title={intl.formatMessage({
          id: 'pages.authorizers.historicalCodeAddressList',
          defaultMessage: '历史代码地址列表',
        })}
        open={showDetail}
        onCancel={() => {
          setCurrentRow(undefined);
          setShowDetail(false);
        }}
        footer={null}
        width={800}
      >
        {currentRow?.historical_code_address && (
          <div style={{ marginTop: 20 }}>
            {currentRow.historical_code_address && currentRow.historical_code_address.length > 0 ? (
              <div>
                {(currentRow.historical_code_address as string[]).map((address, index) => (
                  <Tooltip key={index} title={
                    <span>
                      {address}
                      <a href={`${EXPLORER_URL}/address/${address}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                        <LinkOutlined />
                      </a>
                    </span>
                  }>
                    <Tag color="purple" style={{ marginBottom: '8px', marginRight: '8px' }}>{`${formatAddress(address)}`}</Tag>
                  </Tooltip>
                ))}
              </div>
            ) : (
              <p>{intl.formatMessage({
                id: 'pages.authorizers.noHistoricalCodeAddress',
                defaultMessage: '无历史代码地址',
              })}</p>
            )}
          </div>
        )}
      </Modal>
    </PageContainer>
  );
};

export default Authorizers; 