import { ProColumns, ActionType } from '@ant-design/pro-components';
import {
  PageContainer,
  ProTable,
} from '@ant-design/pro-components';
import { FormattedMessage, useIntl } from '@umijs/max';
import { Tag, Tooltip, Button, Modal, Descriptions, Space, Typography } from 'antd';
import { LinkOutlined } from '@ant-design/icons';
import React, { useRef, useState, useEffect } from 'react';
import { getCodesByEthBalance, getCodesByAuthorizerCount, CodeItem, CodeInfoItem } from '@/services/api';
import { getChainConfig } from '@/services/config';
import tagColorMap from '@/utils/tagColorMap';

// 定义代码详情类型
interface CodeInfo {
  address: string;
  name: string;
  provider: string;
  code: string;
  repo: string;
  contractAccountStandard: string | boolean;
  verificationMethod: string;
  batchCall: string | boolean;
  executor: string | boolean;
  receiveETH: string | boolean;
  receiveNFT: string | boolean;
  recovery: string | boolean;
  sessionKey: string | boolean;
  storage: string;
  nativeETHApprovalAndTransfer: string | boolean;
  hooks: string | boolean;
  signature: string;
  txInitiationMethod: string;
  feePaymentMethod: string;
  upgradable: string | boolean;
  modularContractAccount: string | boolean;
  moduleRegistry: string | boolean;
  isContractAddress: boolean;
  production: string | boolean;
  tags?: string[]; // 添加标签字段
  [key: string]: any; // 索引签名，允许其他可能的属性
}

// 标签颜色映射
// 删除本地定义的tagColorMap

const Codes: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [sortApi, setSortApi] = useState<'eth_balance' | 'authorizer_count'>('eth_balance');
  const [codeInfos, setCodeInfos] = useState<CodeInfo[]>([]);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [currentCode, setCurrentCode] = useState<CodeInfo | null>(null);
  const { EXPLORER_URL } = getChainConfig();

  /**
   * @en-US International configuration
   * @zh-CN 国际化配置
   * */
  const intl = useIntl();
  const { Text, Link } = Typography;


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
      title: intl.formatMessage({
        id: 'pages.codes.eth_balance',
        defaultMessage: 'ETH Balance',
      }),
      dataIndex: 'eth_balance',
      sorter: true,
      sortDirections: ['descend', 'ascend'],
      defaultSortOrder: sortApi === 'eth_balance' ? 'descend' : undefined,
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
            <Tag color={tagColorMap[tag] || 'default'} key={tag}>
              {tag}
            </Tag>
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
  const renderCodeDetail = (code: CodeInfo | null) => {
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
    const renderWithExtra = (value: boolean | string, extraValue?: string) => {
      // 如果值是类似 "true (ERC-7821)" 这样的格式，需要先提取布尔值部分
      let baseValue = value;
      if (typeof value === 'string') {
        if (value.toLowerCase().startsWith('true')) {
          baseValue = true;
        } else if (value.toLowerCase().startsWith('false')) {
          baseValue = false;
        }
      }
      
      // 显示基本值（是/否标签）
      const renderedBaseValue = renderBooleanOrText(baseValue);
      
      // 如果有额外信息，则在下面显示
      if (!extraValue) {
        // 如果原始值是字符串且包含括号，提取括号内的额外信息
        if (typeof value === 'string') {
          const match = value.match(/\((.*?)\)/);
          if (match && match[1]) {
            extraValue = match[1];
          }
        }
      }
      
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
          {code.provider || '-'}
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
          {code.verificationMethod || '-'}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.batchCall',
            defaultMessage: 'Batch Call',
          })}
        >
          {renderBooleanOrText(code.batchCall)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.executor',
            defaultMessage: 'Executor',
          })}
        >
          {renderBooleanOrText(code.executor)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.receiveETH',
            defaultMessage: 'Receive ETH',
          })}
        >
          {renderBooleanOrText(code.receiveETH)}
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
          {renderBooleanOrText(code.recovery)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.sessionKey',
            defaultMessage: 'Session Key',
          })}
        >
          {renderBooleanOrText(code.sessionKey)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.storage',
            defaultMessage: 'Storage',
          })}
        >
          {code.storage || '-'}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.nativeETHApprovalAndTransfer',
            defaultMessage: 'Native ETH Approval & Transfer',
          })}
        >
          {renderBooleanOrText(code.nativeETHApprovalAndTransfer)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.hooks',
            defaultMessage: 'Hooks',
          })}
        >
          {renderBooleanOrText(code.hooks)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.signature',
            defaultMessage: 'Signature',
          })}
        >
          {code.signature || '-'}
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
          {renderBooleanOrText(code.upgradable)}
        </Descriptions.Item>
        <Descriptions.Item 
          label={intl.formatMessage({
            id: 'pages.codes.modularContractAccount',
            defaultMessage: 'Modular Contract Account',
          })}
        >
          {renderBooleanOrText(code.modularContractAccount)}
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
            id: 'pages.codes.tags',
            defaultMessage: 'Tags',
          })}
          span={2}
        >
          <Space wrap>
            {code.tags && code.tags.map((tag: string) => (
              <Tag color={tagColorMap[tag] || 'default'} key={tag}>
                {tag}
              </Tag>
            ))}
          </Space>
        </Descriptions.Item>
      </Descriptions>
    );
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