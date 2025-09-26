import { PlusOutlined, ArrowRightOutlined, LinkOutlined, SearchOutlined } from '@ant-design/icons';
import type { ActionType, ProColumns, ProDescriptionsItemProps } from '@ant-design/pro-components';
import {
  PageContainer,
  ProDescriptions,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl, history, useLocation } from '@umijs/max';
import { Modal, Tag, Tooltip, Input, Button, Card, Row, Col } from 'antd';
import React, { useRef, useState, useEffect } from 'react';
import { getTransactions, TransactionItem } from '@/services/api';
import { getChainConfig } from '@/services/config';
import numeral from 'numeral';

const Transactions: React.FC = () => {
  const [showDetail, setShowDetail] = useState<boolean>(false);
  const actionRef = useRef<ActionType>();
  const [currentRow, setCurrentRow] = useState<TransactionItem>();
  const [searchValue, setSearchValue] = useState<string>('');
  const [searchByParam, setSearchByParam] = useState<string>('');
  const location = useLocation();

  /**
   * @en-US International configuration
   * @zh-CN 国际化配置
   * */
  const intl = useIntl();
  const { EXPLORER_URL } = getChainConfig();

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

  const columns: ProColumns<TransactionItem>[] = [
    {
      title: intl.formatMessage({
        id: 'pages.transactions.block_number',
        defaultMessage: 'Block Number',
      }),
      dataIndex: 'block_number',
      sorter: true,
      sortDirections: ['descend', 'ascend'],
      defaultSortOrder: 'descend',
    },
    {
      title: intl.formatMessage({
        id: 'pages.transactions.timestamp',
        defaultMessage: 'Timestamp',
      }),
      dataIndex: 'timestamp',
      valueType: 'dateTime',
      sorter: true,
      sortDirections: ['descend', 'ascend'],
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
      render: (dom) => {
        if (typeof dom === 'string' && dom.length > 10) {
          const formattedHash = `${dom.substring(0, 6)}...${dom.substring(dom.length - 4)}`;
          return (
            <Tooltip title={
              <span>
                {dom}
                <a href={`${EXPLORER_URL}/tx/${dom}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                  <LinkOutlined />
                </a>
              </span>
            }>
              <Tag color="orange">{formattedHash}</Tag>
            </Tooltip>
          );
        }
        return <Tag color="orange">{dom}</Tag>;
      },
    },
    {
      title: intl.formatMessage({
        id: 'pages.transactions.relayer_address',
        defaultMessage: 'Relayer Address',
      }),
      dataIndex: 'relayer_address',
      render: (dom) => {
        if (typeof dom === 'string' && dom.length > 10) {
          const formattedAddress = `${dom.substring(0, 6)}...${dom.substring(dom.length - 4)}`;
          return (
            <Tooltip title={
              <span>
                {dom}
                <a href={`${EXPLORER_URL}/address/${dom}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                  <LinkOutlined />
                </a>
              </span>
            }>
              <Tag color="purple">{formattedAddress}</Tag>
            </Tooltip>
          );
        }
        return <Tag color="purple">{dom}</Tag>;
      },
    },
    {
      title: intl.formatMessage({
        id: 'pages.transactions.authorization_fee',
        defaultMessage: 'Authorization Fee (ETH)',
      }),
      dataIndex: 'authorization_fee',
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
      title: (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {intl.formatMessage({
            id: 'pages.transactions.authorization_list',
            defaultMessage: 'Authorization List',
          })}
          <div style={{ fontSize: '12px', fontWeight: 'normal' }}>
            <Tag color="blue" size="small" style={{ fontWeight: 'normal' }}>Authorizer</Tag>
            <Tag color="green" size="small" style={{ fontWeight: 'normal' }}>Code</Tag>
          </div>
        </div>
      ),
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
                  <Tooltip title={
                    <span>
                      {auth.authorizer_address}
                      <a href={`${EXPLORER_URL}/address/${auth.authorizer_address}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                        <LinkOutlined />
                      </a>
                    </span>
                  }>
                    <Tag color="blue">{formatAddress(auth.authorizer_address)}</Tag>
                  </Tooltip>
                  <Tooltip title={
                    <span>
                      {auth.code_address}
                      <a href={`${EXPLORER_URL}/address/${auth.code_address}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                        <LinkOutlined />
                      </a>
                    </span>
                  }>
                    <Tag color="green">{formatAddress(auth.code_address)}</Tag>
                  </Tooltip>
                  {auth.nonce === 0 && (
                    <Tooltip title={
                      <span>
                        {intl.formatMessage({
                          id: 'pages.transactions.newEOA',
                          defaultMessage: 'New Account with nonce=0',
                        })}
                      </span>
                    }>
                      <Tag color="red">
                        {intl.formatMessage({
                          id: 'pages.transactions.newEOATag',
                          defaultMessage: 'NewEOA',
                        })}
                      </Tag>
                    </Tooltip>
                  )}
                  {auth.chain_id === 0 && (
                    <Tooltip title={
                      <span>
                        {intl.formatMessage({
                          id: 'pages.transactions.crossAuth',
                          defaultMessage: 'Cross-chain Authentication with chainId=0',
                        })}
                      </span>
                    }>
                      <Tag color="red">
                        {intl.formatMessage({
                          id: 'pages.transactions.crossAuthTag',
                          defaultMessage: 'CrossAuth',
                        })}
                      </Tag>
                    </Tooltip>
                  )}
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
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col flex="auto">
            <Input
              placeholder={intl.formatMessage({
                id: 'pages.transactions.search.placeholder',
                defaultMessage: '输入交易哈希、中继地址、授权者地址或代码地址',
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
                id: 'pages.transactions.search.button',
                defaultMessage: '搜索',
              })}
            </Button>
          </Col>
        </Row>
      </Card>

      <ProTable<TransactionItem>
        headerTitle={intl.formatMessage({
          id: 'pages.transactions.headerTitle',
          defaultMessage: 'Transaction List',
        })}
        actionRef={actionRef}
        rowKey="tx_hash"
        search={false}
        request={async (params, sort) => {
          // 将ProTable的params转换为后端API所需的格式
          const { current, pageSize, ...rest } = params;
          
          // 处理排序参数
          let orderParam = 'desc'; // 默认倒序
          if (sort && Object.keys(sort).length > 0) {
            // 获取第一个排序字段
            const sortField = Object.keys(sort)[0];
            const sortOrder = sort[sortField] === 'ascend' ? 'asc' : 'desc';
            orderParam = sortOrder;
          }
          
          const msg = await getTransactions({
            page: current,
            page_size: pageSize,
            order: orderParam,
            search_by: searchByParam.toLowerCase(),
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

      <Modal
        title={intl.formatMessage({
          id: 'pages.transactions.authorizationList',
          defaultMessage: 'Authorization List',
        })}
        open={showDetail}
        onCancel={() => {
          setCurrentRow(undefined);
          setShowDetail(false);
        }}
        footer={null}
        width={800}
      >
        {currentRow?.authorization_list && (
          <div style={{ marginTop: 20 }}>
            {currentRow.authorization_list && currentRow.authorization_list.length > 0 ? (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr>
                    <th style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid #f0f0f0' }}>
                      {intl.formatMessage({
                        id: 'pages.transactions.authorizerAddress',
                        defaultMessage: 'Authorizer Address',
                      })}
                    </th>
                    <th style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid #f0f0f0' }}>
                      {intl.formatMessage({
                        id: 'pages.transactions.codeAddress',
                        defaultMessage: 'Code Address',
                      })}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {currentRow.authorization_list.map((auth, index) => (
                    <tr key={index} style={{ borderBottom: '1px solid #f0f0f0' }}>
                      <td style={{ padding: '8px' }}>
                        <Tooltip title={
                          <span>
                            {auth.authorizer_address}
                            <a href={`${EXPLORER_URL}/address/${auth.authorizer_address}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                              <LinkOutlined />
                            </a>
                          </span>
                        }>
                          <Tag color="blue">{formatAddress(auth.authorizer_address)}</Tag>
                        </Tooltip>
                        {auth.nonce === 0 && (
                          <Tooltip title={
                            <span>
                              {intl.formatMessage({
                                id: 'pages.transactions.newEOA',
                                defaultMessage: 'New Account with nonce=0',
                              })}
                            </span>
                          }>
                            <Tag color="red">
                              {intl.formatMessage({
                                id: 'pages.transactions.newEOATag',
                                defaultMessage: 'NewEOA',
                              })}
                            </Tag>
                          </Tooltip>
                        )}
                        {auth.chain_id === 0 && (
                          <Tooltip title={
                            <span>
                              {intl.formatMessage({
                                id: 'pages.transactions.crossAuth',
                                defaultMessage: 'Cross-chain Authentication with chainId=0',
                              })}
                            </span>
                          }>
                            <Tag color="red">
                              {intl.formatMessage({
                                id: 'pages.transactions.crossAuthTag',
                                defaultMessage: 'CrossAuth',
                              })}
                            </Tag>
                          </Tooltip>
                        )}
                      </td>
                      <td style={{ padding: '8px' }}>
                        <Tooltip title={
                          <span>
                            {auth.code_address}
                            <a href={`${EXPLORER_URL}/address/${auth.code_address}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                              <LinkOutlined />
                            </a>
                          </span>
                        }>
                          <Tag color="green">{formatAddress(auth.code_address)}</Tag>
                        </Tooltip>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p>{intl.formatMessage({
                id: 'pages.transactions.noAuthorizationData',
                defaultMessage: 'No Authorization Data',
              })}</p>
            )}
          </div>
        )}
      </Modal>
    </PageContainer>
  );
};

export default Transactions;
