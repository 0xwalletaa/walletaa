import { SearchOutlined, LinkOutlined } from '@ant-design/icons';
import type { ActionType, ProColumns } from '@ant-design/pro-components';
import {
  PageContainer,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl, history, useLocation } from '@umijs/max';
import { Tag, Tooltip, Input, Button, Card, Row, Col, Result } from 'antd';
import React, { useRef, useState, useEffect } from 'react';
import { getCalls, CallItem } from '@/services/api';
import { getChainConfig, getCurrentChain } from '@/services/config';
import numeral from 'numeral';
import { ethers } from 'ethers';

// 函数签名映射（选择器 => 完整函数签名）
const FUNCTION_SIGNATURES: string[] = [
  'execute(bytes32,bytes)',
  'initialize()',
  'isValidSignature(bytes32,bytes)',
  'onERC721Received(address,address,uint256,bytes)',
  'onERC1155Received(address,address,uint256,uint256,bytes)',
];

// 使用ethers动态计算函数选择器
const FUNCTION_SELECTORS: Record<string, string> = {};
FUNCTION_SIGNATURES.forEach(signature => {
  const selector = ethers.id(signature).slice(0, 10);
  FUNCTION_SELECTORS[selector] = signature;
});

const Traces: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [searchValue, setSearchValue] = useState<string>('');
  const [searchByParam, setSearchByParam] = useState<string>('');
  const location = useLocation();

  /**
   * @en-US International configuration
   * @zh-CN 国际化配置
   * */
  const intl = useIntl();
  const { EXPLORER_URL } = getChainConfig();
  const currentChain = getCurrentChain();

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

  // 解析函数选择器
  const parseFunctionSelector = (selector: string) => {
    const functionName = FUNCTION_SELECTORS[selector];
    return functionName || selector;
  };

  const columns: ProColumns<CallItem>[] = [
    {
      title: intl.formatMessage({
        id: 'pages.traces.block_number',
        defaultMessage: 'Block Number',
      }),
      dataIndex: 'block_number',
      sorter: true,
      sortDirections: ['descend', 'ascend'],
      defaultSortOrder: 'descend',
    },
    {
      title: intl.formatMessage({
        id: 'pages.traces.timestamp',
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
        id: 'pages.traces.tx_hash',
        defaultMessage: 'Transaction Hash',
      }),
      dataIndex: 'tx_hash',
      render: (dom: any) => {
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
        id: 'pages.traces.call_type_trace_address',
        defaultMessage: 'Call Type & Trace',
      }),
      dataIndex: 'call_type_trace_address',
      render: (dom: any) => {
        if (typeof dom === 'string') {
          // 如果以下划线结尾，则移除末尾的下划线
          const cleanedValue = dom.endsWith('_') ? dom.slice(0, -1) : dom;
          return cleanedValue;
        }
        return dom;
      },
    },
    {
      title: intl.formatMessage({
        id: 'pages.traces.from_address',
        defaultMessage: 'From Address',
      }),
      dataIndex: 'from_address',
      render: (dom: any) => {
        if (typeof dom === 'string' && dom.length > 10) {
          const formattedAddress = formatAddress(dom);
          return (
            <Tooltip title={
              <span>
                {dom}
                <a href={`${EXPLORER_URL}/address/${dom}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                  <LinkOutlined />
                </a>
              </span>
            }>
              <Tag color="default">{formattedAddress}</Tag>
            </Tooltip>
          );
        }
        return <Tag color="default">{dom}</Tag>;
      },
    },
    {
      title: intl.formatMessage({
        id: 'pages.traces.authorizer_address',
        defaultMessage: 'Authorizer Address',
      }),
      dataIndex: 'original_code_address',
      render: (dom: any) => {
        if (typeof dom === 'string' && dom.length > 10) {
          const formattedAddress = formatAddress(dom);
          return (
            <Tooltip title={
              <span>
                {dom}
                <a href={`${EXPLORER_URL}/address/${dom}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                  <LinkOutlined />
                </a>
              </span>
            }>
              <Tag color="blue">{formattedAddress}</Tag>
            </Tooltip>
          );
        }
        return <Tag color="blue">{dom}</Tag>;
      },
    },
    {
      title: intl.formatMessage({
        id: 'pages.traces.code_address',
        defaultMessage: 'Code Address',
      }),
      dataIndex: 'parsed_code_address',
      render: (dom: any) => {
        if (typeof dom === 'string' && dom.length > 10) {
          const formattedAddress = formatAddress(dom);
          return (
            <Tooltip title={
              <span>
                {dom}
                <a href={`${EXPLORER_URL}/address/${dom}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                  <LinkOutlined />
                </a>
              </span>
            }>
              <Tag color="green">{formattedAddress}</Tag>
            </Tooltip>
          );
        }
        return <Tag color="green">{dom}</Tag>;
      },
    },
    {
      title: intl.formatMessage({
        id: 'pages.traces.calling_function',
        defaultMessage: 'Calling Function',
      }),
      dataIndex: 'calling_function',
      width: 280,
      render: (dom: any) => {
        if (typeof dom === 'string') {
          const parsedFunction = parseFunctionSelector(dom);
          const isKnownFunction = FUNCTION_SELECTORS[dom];
          
          if (isKnownFunction) {
            return (
              <Tooltip title={`Function: ${parsedFunction} | Selector: ${dom}`}>
                <Tag color="magenta" style={{ 
                  maxWidth: '260px', 
                  overflow: 'hidden', 
                  textOverflow: 'ellipsis', 
                  whiteSpace: 'nowrap',
                  display: 'inline-block'
                }}>
                  {parsedFunction}
                </Tag>
              </Tooltip>
            );
          } else {
            return <Tag color="magenta">{dom}</Tag>;
          }
        }
        return dom;
      },
    },
  ];

  // 如果不是mainnet，显示暂不支持
  if (currentChain !== 'mainnet') {
    return (
      <PageContainer>
        <Result
          status="info"
          title={intl.formatMessage({
            id: 'pages.traces.notSupported.title',
            defaultMessage: '暂不支持',
          })}
          subTitle={intl.formatMessage({
            id: 'pages.traces.notSupported.subtitle', 
            defaultMessage: 'Calls功能目前仅在主网(Mainnet)支持',
          })}
        />
      </PageContainer>
    );
  }

  return (
    <PageContainer>
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col flex="auto">
            <Input
              placeholder={intl.formatMessage({
                id: 'pages.traces.search.placeholder',
                defaultMessage: '输入原始代码地址或解析代码地址',
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
                id: 'pages.traces.search.button',
                defaultMessage: '搜索',
              })}
            </Button>
          </Col>
        </Row>
      </Card>

      <ProTable<CallItem>
        headerTitle={intl.formatMessage({
          id: 'pages.traces.headerTitle',
          defaultMessage: 'Call List',
        })}
        actionRef={actionRef}
        rowKey={(record) => `${record.tx_hash}_${record.call_type_trace_address}`}
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
          
          const msg = await getCalls({
            page: current,
            page_size: pageSize,
            order: orderParam,
            search_by: searchByParam.toLowerCase(),
            ...rest,
          });
          return {
            data: msg.calls || [],
            success: true,
            total: msg.total || 0,
          };
        }}
        columns={columns}
      />
    </PageContainer>
  );
};

export default Traces;
