import { ProColumns, ActionType } from '@ant-design/pro-components';
import {
  PageContainer,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl, history, useLocation } from '@umijs/max';
import { Tag, Tooltip, Button, Modal, Descriptions, Space, Typography, Input, Card, Row, Col } from 'antd';
import { LinkOutlined, SearchOutlined, InfoCircleOutlined } from '@ant-design/icons';
import React, { useRef, useState, useEffect } from 'react';
import { getCodesByTvlBalance, getCodesByAuthorizerCount, CodeItem, CodeInfoItem } from '@/services/api';
import { getChainConfig } from '@/services/config';
import tagInfoMap from '@/utils/tagInfoMap';
import numeral from 'numeral';

// 标签颜色映射
// 已更新为使用 tagInfoMap

const Codes: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [sortApi, setSortApi] = useState<'tvl_balance' | 'authorizer_count'>('tvl_balance');
  const [codeInfos, setCodeInfos] = useState<CodeInfoItem[]>([]);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [currentCode, setCurrentCode] = useState<CodeInfoItem | null>(null);
  const [searchValue, setSearchValue] = useState<string>('');
  const [searchByParam, setSearchByParam] = useState<string>('');
  const { EXPLORER_URL } = getChainConfig();
  const location = useLocation();

  /**
   * @en-US International configuration
   * @zh-CN 国际化配置
   * */
  const intl = useIntl();
  const { Text, Link } = Typography;

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

  // 处理显示详情 - 使用record中的details字段
  const handleViewDetails = (record: CodeItem) => {
    if (record.details) {
      setCurrentCode(record.details);
      setModalVisible(true);
    }
  };

  // 检查是否有详情可以显示
  const hasDetails = (record: CodeItem) => {
    return record.details !== null && record.details !== undefined;
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
        id: 'pages.codes.provider',
        defaultMessage: 'Provider',
      }),
      dataIndex: 'code_address',
      render: (_, record) => {
        return record.provider ? (
          <Tag color="volcano">{record.provider}</Tag>
        ) : null;
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
      sortDirections: ['descend', 'ascend'],
      defaultSortOrder: sortApi === 'authorizer_count' ? 'descend' : undefined,
    },
    {
      title: (
        <Space>
          {intl.formatMessage({
            id: 'pages.codes.tvl_balance',
            defaultMessage: 'TVL',
          })}
          <Tooltip title="TVL = ETH + WETH + WBTC + USDT + USDC + DAI">
            <InfoCircleOutlined style={{ color: 'rgba(0,0,0,.45)' }} />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'tvl_balance',
      sorter: true,
      sortDirections: ['descend', 'ascend'],
      defaultSortOrder: sortApi === 'tvl_balance' ? 'descend' : undefined,
      align: 'right',
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
        id: 'pages.codes.tags',
        defaultMessage: 'Tags',
      }),
      dataIndex: 'tags',
      render: (_, record) => (
        <Space wrap>
          {record.tags && record.tags.map((tag: string) => (
            <Tooltip
              key={tag}
              title={
                tagInfoMap[tag] ? (
                  <span>
                    {tagInfoMap[tag].description}
                    <a 
                      href={tagInfoMap[tag].link} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      style={{ marginLeft: 8, color: 'white' }}
                    >
                      <LinkOutlined />
                    </a>
                  </span>
                ) : tag
              }
            >
              <Tag color={tagInfoMap[tag]?.color || 'default'}>
                {tag}
              </Tag>
            </Tooltip>
          ))}
        </Space>
      ),
    },
    {
      title: intl.formatMessage({
        id: 'pages.codes.details',
        defaultMessage: 'Details',
      }),
      dataIndex: 'code_address',
      valueType: 'option',
      render: (_, record) => (
        hasDetails(record) ? (
          <Button 
            type="link" 
            onClick={() => handleViewDetails(record)}
          >
            {intl.formatMessage({
              id: 'pages.codes.view_details',
              defaultMessage: 'View Details',
            })}
          </Button>
        ) : null
      ),
    },
  ];

  // 动态设置表格标题
  const getHeaderTitle = () => {
    return intl.formatMessage({
      id: 'pages.codes.headerTitle',
      defaultMessage: 'Code List',
    });
  };

  // 渲染代码详情内容
  const renderCodeDetail = (code: CodeInfoItem | null) => {
    if (!code) return null;

    const renderBooleanOrText = (value: boolean | string) => {
      if (typeof value === 'boolean') {
        return value ? (
          <Tag color="green">
            {intl.formatMessage({
              id: 'pages.codes.yes',
              defaultMessage: 'Yes',
            })}
          </Tag>
        ) : (
          <Tag color="red">
            {intl.formatMessage({
              id: 'pages.codes.no',
              defaultMessage: 'No',
            })}
          </Tag>
        );
      }
      if (value === '') return '-';
      return value;
    };

    const renderLink = (url: string) => {
      if (!url || url === '' || url === 'closed-source') return '-';
      return <Link href={url} target="_blank">{url}</Link>;
    };

    // 用于渲染带有Extra信息的字段
    const renderWithExtra = (value: boolean | string | undefined, extraValue?: string) => {
      // 如果值为undefined，返回'-'
      if (value === undefined) return '-';
      
      // 如果值是类似 "true (ERC-7821)" 这样的格式，需要先提取布尔值部分
      let baseValue = value;
      if (typeof value === 'string') {
        if (value.toLowerCase() == 'true') {
          baseValue = true;
        } else if (value.toLowerCase() == 'false') {
          baseValue = false;
        }
      }
      
      // 显示基本值（是/否标签）
      const renderedBaseValue = renderBooleanOrText(baseValue);
      
      // 如果没有extraValue，就直接返回基本值
      if (!extraValue) return renderedBaseValue;
      
      return (
        <Space direction="vertical" size={0}>
          {renderedBaseValue}
          {extraValue && <Text type="secondary" style={{ fontSize: '12px' }}>{extraValue}</Text>}
        </Space>
      );
    };

    return (
      <Descriptions bordered column={2}>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.address',
            defaultMessage: 'Address',
          })} 
          span={2}
        >
          {code.address}
          <a href={`${EXPLORER_URL}/address/${code.address}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8 }}>
            <LinkOutlined />
          </a>
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.name',
            defaultMessage: 'Name',
          })} 
          span={2}
        >
          {code.name || '-'}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.provider',
            defaultMessage: 'Provider',
          })}
        >
          {code.provider ? <Tag color="volcano">{code.provider}</Tag> : '-'}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.code',
            defaultMessage: 'Code',
          })}
        >
          {renderLink(code.code)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.repo',
            defaultMessage: 'Repository',
          })}
        >
          {renderLink(code.repo)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.contractAccountStandard',
            defaultMessage: 'Contract Account Standard',
          })}
        >
          {code.contractAccountStandard || '-'}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.verificationMethod',
            defaultMessage: 'Verification Method',
          })}
        >
          {renderWithExtra(code.verificationMethod, code.verificationMethodExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.batchCall',
            defaultMessage: 'Batch Call',
          })}
        >
          {renderWithExtra(code.batchCall, code.batchCallExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.executor',
            defaultMessage: 'Executor',
          })}
        >
          {renderWithExtra(code.executor, code.executorExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.receiveETH',
            defaultMessage: 'Receive ETH',
          })}
        >
          {renderWithExtra(code.receiveETH, code.receiveETHExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.receiveNFT',
            defaultMessage: 'Receive NFT',
          })}
        >
          {renderBooleanOrText(code.receiveNFT)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.recovery',
            defaultMessage: 'Recovery',
          })}
        >
          {renderWithExtra(code.recovery, code.recoveryExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.sessionKey',
            defaultMessage: 'Session Key',
          })}
        >
          {renderWithExtra(code.sessionKey, code.sessionKeyExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.storage',
            defaultMessage: 'Storage',
          })}
        >
          {renderWithExtra(code.storage, code.storageExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.nativeETHApprovalAndTransfer',
            defaultMessage: 'Native ETH Approval & Transfer',
          })}
        >
          {renderWithExtra(code.nativeETHApprovalAndTransfer, code.nativeETHApprovalAndTransferExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.hooks',
            defaultMessage: 'Hooks',
          })}
        >
          {renderWithExtra(code.hooks, code.hooksExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.signature',
            defaultMessage: 'Signature',
          })}
        >
          {renderWithExtra(code.signature, code.signatureExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.txInitiationMethod',
            defaultMessage: 'Tx Initiation Method',
          })}
        >
          {code.txInitiationMethod || '-'}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.feePaymentMethod',
            defaultMessage: 'Fee Payment Method',
          })}
        >
          {code.feePaymentMethod || '-'}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.upgradable',
            defaultMessage: 'Upgradable',
          })}
        >
          {renderWithExtra(code.upgradable, code.upgradableExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.modularContractAccount',
            defaultMessage: 'Modular Contract Account',
          })}
        >
          {renderWithExtra(code.modularContractAccount, code.modularContractAccountExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.moduleRegistry',
            defaultMessage: 'Module Registry',
          })}
        >
          {renderBooleanOrText(code.moduleRegistry)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.isContractAddress',
            defaultMessage: 'Is Contract Address',
          })}
        >
          {renderBooleanOrText(code.isContractAddress)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.production',
            defaultMessage: 'Production',
          })}
        >
          {renderBooleanOrText(code.production)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.audit',
            defaultMessage: 'Audit',
          })}
        >
          {renderWithExtra(code.audit, code.auditExtra)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.usage',
            defaultMessage: 'Usage',
          })}
        >
          {code.usage || '-'}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.tags',
            defaultMessage: 'Tags',
          })}
          span={2}
        >
          <Space wrap>
            {code.tags && code.tags.map((tag: string) => (
              <Tooltip
                key={tag}
                title={
                  tagInfoMap[tag] ? (
                    <span>
                      {tagInfoMap[tag].description}
                      <a 
                        href={tagInfoMap[tag].link} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        style={{ marginLeft: 8, color: 'white' }}
                      >
                        <LinkOutlined />
                      </a>
                    </span>
                  ) : tag
                }
              >
                <Tag color={tagInfoMap[tag]?.color || 'default'}>
                  {tag}
                </Tag>
              </Tooltip>
            ))}
          </Space>
        </Descriptions.Item>
      </Descriptions>
    );
  };

  return (
    <PageContainer>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col flex="auto">
            <Input
              placeholder={intl.formatMessage({
                id: 'pages.codes.search.placeholder',
                defaultMessage: '输入代码地址或提供者名称',
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
                id: 'pages.codes.search.button',
                defaultMessage: '搜索',
              })}
            </Button>
          </Col>
        </Row>
      </Card>
      
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
            const sortOrder = sort[sortField] === 'ascend' ? 'asc' : 'desc';
            
            // 根据排序字段选择API
            if (sortField === 'tvl_balance') {
              selectedApi = 'tvl_balance';
              setSortApi('tvl_balance');
            } else if (sortField === 'authorizer_count') {
              selectedApi = 'authorizer_count';
              setSortApi('authorizer_count');
            }
            
            orderParam = sortOrder;
          }

          // 根据选择的API调用不同的接口
          let msg;
          if (selectedApi === 'tvl_balance') {
            msg = await getCodesByTvlBalance({
              page: current,
              page_size: pageSize,
              order: orderParam,
              search_by: searchByParam.toLowerCase(),
              ...rest,
            });
          } else {
            msg = await getCodesByAuthorizerCount({
              page: current,
              page_size: pageSize,
              order: orderParam,
              search_by: searchByParam.toLowerCase(),
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

      <Modal
        title={intl.formatMessage({
          id: 'pages.codes.detail_title',
          defaultMessage: 'Contract Details',
        })}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)}>
            {intl.formatMessage({
              id: 'pages.codes.close',
              defaultMessage: 'Close',
            })}
          </Button>
        ]}
        width={800}
      >
        {renderCodeDetail(currentCode)}
      </Modal>
    </PageContainer>
  );
};

export default Codes; 