import { InfoCircleOutlined, LinkOutlined } from '@ant-design/icons';
import { PageContainer } from '@ant-design/pro-components';
import { useIntl } from '@umijs/max';
import { Card, Col, Row, Table, Tooltip, Tag, Button, Modal, Descriptions, Typography, Space } from 'antd';
import { Area, Column } from '@ant-design/plots';
import numeral from 'numeral';
import React, { useEffect, useState, ReactNode } from 'react';
import { getOverview, Overview, CodeInfoItem } from '@/services/api';
import { getChainConfig, getUrlWithChain } from '@/services/config';
import tagColorMap from '@/utils/tagColorMap';
import { history } from '@umijs/max';

// 定义ChartCard组件的属性类型
interface ChartCardProps {
  loading?: boolean;
  title: string;
  total?: string | number | ReactNode;
  contentHeight?: number;
  footer?: ReactNode;
  children?: ReactNode;
  bordered?: boolean;
}

// 定义Field组件的属性类型
interface FieldProps {
  label: string;
  value: string | number;
}

// 定义图表数据类型
interface ChartDataItem {
  x: string;
  y: number;
}

// 引入ChartCard和Field组件
const ChartCard: React.FC<ChartCardProps> = ({ loading, title, total, contentHeight = 46, footer, children, bordered = true }) => {
  const intl = useIntl();
  return (
    <Card
      loading={loading}
      bordered={bordered}
      title={title}
      bodyStyle={{ padding: '20px 24px 8px 24px' }}
    >
      <div style={{ position: 'relative' }}>
        <div style={{ marginBottom: contentHeight ? 12 : 0 }}>
          <div
            style={{
              margin: '0 0 4px 0',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>{title}</div>
            <Tooltip title={intl.formatMessage({ id: 'pages.welcome.dataDescription' })}>
              <InfoCircleOutlined style={{ color: 'rgba(0,0,0,.45)' }} />
            </Tooltip>
          </div>
          <div style={{ fontSize: '30px', lineHeight: '38px', color: 'rgba(0,0,0,.85)', marginBottom: 4 }}>
            {total}
          </div>
        </div>
        {children && (
          <div style={{ height: contentHeight }}>
            {children}
          </div>
        )}
        {footer && (
          <div
            style={{
              margin: '8px 0 0 0',
              borderTop: '1px solid #e8e8e8',
              paddingTop: 9,
            }}
          >
            {footer}
          </div>
        )}
      </div>
    </Card>
  );
};

const Field: React.FC<FieldProps> = ({ label, value }) => (
  <div style={{ display: 'inline-block', marginRight: 8 }}>
    <span style={{ color: 'rgba(0,0,0,.45)' }}>{label}</span>
    <span style={{ marginLeft: 8 }}>{value}</span>
  </div>
);

const topColResponsiveProps = {
  xs: 24,
  sm: 12,
  md: 12,
  lg: 12,
  xl: 6,
  style: {
    marginBottom: 24,
  },
};

const Welcome: React.FC = () => {
  const intl = useIntl();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [currentCode, setCurrentCode] = useState<CodeInfoItem | null>(null);
  const chainConfig = getChainConfig();
  const { Text, Link } = Typography;

  useEffect(() => {
    getOverview()
      .then(data => {
        // 不再需要从code_infos处理数据，直接使用top10_codes中的details和provider字段
        setOverview(data.overview);
        setLoading(false);
      })
      .catch(error => {
        console.error('获取数据失败:', error);
        setLoading(false);
      });
  }, []);

  // 格式化地址显示
  const formatAddress = (address: string) => {
    return typeof address === 'string' && address.length > 10
      ? `${address.substring(0, 6)}...${address.substring(address.length - 4)}`
      : address;
  };

  // 检查是否有详情可以显示
  const hasDetails = (record: any) => {
    return record.details !== null && record.details !== undefined;
  };

  // 处理显示详情
  const handleViewDetails = (record: any) => {
    if (record.details) {
      setCurrentCode(record.details);
      setModalVisible(true);
    }
  };

  // 准备图表数据
  const getDailyTxCountData = (): ChartDataItem[] => {
    if (!overview || !overview.daily_tx_count) return [];
    return Object.entries(overview.daily_tx_count).map(([date, count]) => ({
      x: date,
      y: count,
    }));
  };

  const getDailyAuthCountData = (): ChartDataItem[] => {
    if (!overview || !overview.daily_authorizaion_count) return [];
    return Object.entries(overview.daily_authorizaion_count).map(([date, count]) => ({
      x: date,
      y: count,
    }));
  };

  const getDailyCodeCountData = (): ChartDataItem[] => {
    if (!overview || !overview.daily_code_count) return [];
    return Object.entries(overview.daily_code_count).map(([date, count]) => ({
      x: date,
      y: count,
    }));
  };

  const getDailyRelayerCountData = (): ChartDataItem[] => {
    if (!overview || !overview.daily_relayer_count) return [];
    return Object.entries(overview.daily_relayer_count).map(([date, count]) => ({
      x: date,
      y: count,
    }));
  };

  const getCumulativeTxData = (): ChartDataItem[] => {
    if (!overview || !overview.daily_cumulative_tx_count) return [];
    return Object.entries(overview.daily_cumulative_tx_count).map(([date, count]) => ({
      x: date,
      y: count,
    }));
  };

  const getCumulativeAuthData = (): ChartDataItem[] => {
    if (!overview || !overview.daily_cumulative_authorizaion_count) return [];
    return Object.entries(overview.daily_cumulative_authorizaion_count).map(([date, count]) => ({
      x: date,
      y: count,
    }));
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
        if (value.toLowerCase().startsWith('true')) {
          baseValue = true;
        } else if (value.toLowerCase().startsWith('false')) {
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
          <a href={`${chainConfig.EXPLORER_URL}/address/${code.address}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8 }}>
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
      </Descriptions>
    );
  };

  return (
    <PageContainer title={intl.formatMessage({ id: 'pages.welcome.eip7702Title' })}>
      <Row gutter={24}>
        <Col {...topColResponsiveProps}>
          <ChartCard
            bordered={false}
            title={intl.formatMessage({ id: 'pages.welcome.transactions' })}
            loading={loading}
            total={overview ? numeral(overview.tx_count).format('0,0') : 0}
            contentHeight={46}
          >
            <Column
              xField="x"
              yField="y"
              padding={-20}
              axis={false}
              height={46}
              data={getDailyTxCountData()}
              scale={{ x: { paddingInner: 0.4 } }}
            />
          </ChartCard>
        </Col>

        <Col {...topColResponsiveProps}>
          <ChartCard
            bordered={false}
            loading={loading}
            title={intl.formatMessage({ id: 'pages.welcome.authorizers' })}
            total={overview ? numeral(overview.authorizer_count).format('0,0') : 0}
            contentHeight={46}
          >
            <Column
              xField="x"
              yField="y"
              padding={-20}
              axis={false}
              height={46}
              data={getDailyAuthCountData()}
              scale={{ x: { paddingInner: 0.4 } }}
            />
          </ChartCard>
        </Col>

        <Col {...topColResponsiveProps}>
          <ChartCard
            bordered={false}
            loading={loading}
            title={intl.formatMessage({ id: 'pages.welcome.codes' })}
            total={overview ? numeral(overview.code_count).format('0,0') : 0}
            contentHeight={46}
          >
            <Column
              xField="x"
              yField="y"
              padding={-20}
              axis={false}
              height={46}
              data={getDailyCodeCountData()}
              scale={{ x: { paddingInner: 0.4 } }}
            />
          </ChartCard>
        </Col>

        <Col {...topColResponsiveProps}>
          <ChartCard
            loading={loading}
            bordered={false}
            title={intl.formatMessage({ id: 'pages.welcome.relayers' })}
            total={overview ? numeral(overview.relayer_count).format('0,0') : 0}
            contentHeight={46}
          >
            <Column
              xField="x"
              yField="y"
              padding={-20}
              axis={false}
              height={46}
              data={getDailyRelayerCountData()}
              scale={{ x: { paddingInner: 0.4 } }}
            />
          </ChartCard>
        </Col>
      </Row>

      <Card
        loading={loading}
        bordered={false}
        bodyStyle={{ padding: 0 }}
        style={{ marginBottom: 24 }}
      >
        <div style={{ padding: '24px 24px 0 24px' }}>
          <Row gutter={24}>
            <Col xl={12} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
              <div style={{ position: 'relative' }}>
                <h4 style={{ marginBottom: 20 }}>{intl.formatMessage({ id: 'pages.welcome.cumulativeTxs' })}</h4>
                <Area
                  height={200}
                  data={getCumulativeTxData()}
                  xField="x"
                  yField="y"
                  shapeField="smooth"
                  paddingBottom={12}
                  axis={{
                    x: {
                      title: false,
                    },
                    y: {
                      title: false,
                      gridLineDash: null,
                      gridStroke: '#ccc',
                    },
                  }}
                  tooltip={{
                    name: intl.formatMessage({ id: 'pages.welcome.cumulativeTxs' }),
                    channel: 'y',
                  }}
                />
              </div>
            </Col>
            <Col xl={12} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
              <div style={{ position: 'relative' }}>
                <h4 style={{ marginBottom: 20 }}>{intl.formatMessage({ id: 'pages.welcome.cumulativeAuths' })}</h4>
                <Area
                  height={200}
                  data={getCumulativeAuthData()}
                  xField="x"
                  yField="y"
                  shapeField="smooth"
                  paddingBottom={12}
                  axis={{
                    x: {
                      title: false,
                    },
                    y: {
                      title: false,
                      gridLineDash: null,
                      gridStroke: '#ccc',
                    },
                  }}
                  tooltip={{
                    name: intl.formatMessage({ id: 'pages.welcome.cumulativeAuths' }),
                    channel: 'y',
                  }}
                />
              </div>
            </Col>
          </Row>
        </div>
      </Card>

      <Row gutter={24}>
        <Col xl={24} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
          <Card
            bordered={false}
            title={intl.formatMessage({ id: 'pages.welcome.codeRanking' })}
            loading={loading}
            style={{ height: '100%' }}
            bodyStyle={{ padding: '0 24px 24px 24px' }}
          >
            <Table
              rowKey="code_address"
              size="small"
              columns={[
                {
                  title: intl.formatMessage({ id: 'pages.welcome.ranking' }),
                  dataIndex: 'index',
                  key: 'index',
                  render: (_: any, __: any, index: number) => index + 1,
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.codeAddress' }),
                  dataIndex: 'code_address',
                  key: 'code_address',
                  render: (text: string) => (
                    <Tooltip title={
                      <span>
                        {text}
                        <a href={`${chainConfig.EXPLORER_URL}/address/${text}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                          <LinkOutlined />
                        </a>
                      </span>
                    }>
                      <Tag color="green">{formatAddress(text)}</Tag>
                    </Tooltip>
                  ),
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.provider', defaultMessage: 'Provider' }),
                  dataIndex: 'provider',
                  key: 'provider',
                  render: (text: string) => (
                    text ? <Tag color="volcano">{text}</Tag> : null
                  ),
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.tags', defaultMessage: 'Tags' }),
                  dataIndex: 'tags',
                  key: 'tags',
                  render: (tags: string[]) => (
                    <Space wrap>
                      {tags && tags.map((tag: string) => (
                        <Tag color={tagColorMap[tag] || 'default'} key={tag}>
                          {tag}
                        </Tag>
                      ))}
                    </Space>
                  ),
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.authorizerCount' }),
                  dataIndex: 'authorizer_count',
                  key: 'authorizer_count',
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.tvlBalance' }),
                  dataIndex: 'tvl_balance',
                  key: 'tvl_balance',
                  render: (text: number) => numeral(text).format('0,0.0000'),
                },
                {
                  title: intl.formatMessage({ id: 'pages.codes.details', defaultMessage: 'Details' }),
                  dataIndex: 'code_address',
                  key: 'details',
                  render: (_, record) => (
                    hasDetails(record) ? (
                      <Button 
                        type="link" 
                        onClick={() => handleViewDetails(record)}
                        style={{ padding: '0', height: 'auto', minWidth: 'auto', lineHeight: '1' }}
                      >
                        {intl.formatMessage({
                          id: 'pages.codes.view_details',
                          defaultMessage: 'View Details',
                        })}
                      </Button>
                    ) : null
                  ),
                },
              ]}
              dataSource={overview ? overview.top10_codes : []}
              pagination={false}
              footer={() => (
                <div style={{ textAlign: 'center' }}>
                  <Button type="link" onClick={() => history.push(getUrlWithChain('/codes'))}>
                    {intl.formatMessage({ id: 'pages.welcome.viewAll', defaultMessage: '查看全部' })}
                  </Button>
                </div>
              )}
            />
          </Card>
        </Col>
        <Col xl={12} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
          <Card
            bordered={false}
            title={intl.formatMessage({ id: 'pages.welcome.authorizerRanking', defaultMessage: 'Authorizer Ranking' })}
            loading={loading}
            style={{ height: '100%' }}
            bodyStyle={{ padding: '0 24px 24px 24px' }}
          >
            <Table
              rowKey="authorizer_address"
              size="small"
              columns={[
                {
                  title: intl.formatMessage({ id: 'pages.welcome.ranking', defaultMessage: 'Ranking' }),
                  dataIndex: 'index',
                  key: 'index',
                  render: (_: any, __: any, index: number) => index + 1,
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.authorizerAddress', defaultMessage: 'Authorizer Address' }),
                  dataIndex: 'authorizer_address',
                  key: 'authorizer_address',
                  render: (text: string) => (
                    <Tooltip title={
                      <span>
                        {text}
                        <a href={`${chainConfig.EXPLORER_URL}/address/${text}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                          <LinkOutlined />
                        </a>
                      </span>
                    }>
                      <Tag color="blue">{formatAddress(text)}</Tag>
                    </Tooltip>
                  ),
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.codeAddress', defaultMessage: 'Code Address' }),
                  dataIndex: 'code_address',
                  key: 'code_address',
                  render: (text: string) => (
                    <Tooltip title={
                      <span>
                        {text}
                        <a href={`${chainConfig.EXPLORER_URL}/address/${text}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                          <LinkOutlined />
                        </a>
                      </span>
                    }>
                      <Tag color="green">{formatAddress(text)}</Tag>
                    </Tooltip>
                  ),
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.provider', defaultMessage: 'Provider' }),
                  dataIndex: 'provider',
                  key: 'provider',
                  render: (text: string) => (
                    text ? <Tag color="volcano">{text}</Tag> : null
                  ),
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.tvlBalance', defaultMessage: 'TVL Balance' }),
                  dataIndex: 'tvl_balance',
                  key: 'tvl_balance',
                  render: (text: number) => numeral(text).format('0,0.0000'),
                },
              ]}
              dataSource={overview ? overview.top10_authorizers : []}
              pagination={false}
              footer={() => (
                <div style={{ textAlign: 'center' }}>
                  <Button type="link" onClick={() => history.push(getUrlWithChain('/authorizers'))}>
                    {intl.formatMessage({ id: 'pages.welcome.viewAll', defaultMessage: '查看全部' })}
                  </Button>
                </div>
              )}
            />
          </Card>
        </Col>
        <Col xl={12} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
          <Card
            bordered={false}
            title={intl.formatMessage({ id: 'pages.welcome.relayerRanking' })}
            loading={loading}
            style={{ height: '100%' }}
            bodyStyle={{ padding: '0 24px 24px 24px' }}
          >
            <Table
              rowKey="relayer_address"
              size="small"
              columns={[
                {
                  title: intl.formatMessage({ id: 'pages.welcome.ranking' }),
                  dataIndex: 'index',
                  key: 'index',
                  render: (_: any, __: any, index: number) => index + 1,
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.relayerAddress' }),
                  dataIndex: 'relayer_address',
                  key: 'relayer_address',
                  render: (text: string) => (
                    <Tooltip title={
                      <span>
                        {text}
                        <a href={`${chainConfig.EXPLORER_URL}/address/${text}`} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8, color: 'white' }}>
                          <LinkOutlined />
                        </a>
                      </span>
                    }>
                      <Tag color="purple">{formatAddress(text)}</Tag>
                    </Tooltip>
                  ),
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.txCount' }),
                  dataIndex: 'tx_count',
                  key: 'tx_count',
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.authCount' }),
                  dataIndex: 'authorization_count',
                  key: 'authorization_count',
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.authorizationFee' }),
                  dataIndex: 'authorization_fee',
                  key: 'authorization_fee',
                  render: (text: number) => numeral(text).format('0,0.0000'),
                },
              ]}
              dataSource={overview ? overview.top10_relayers : []}
              pagination={false}
              footer={() => (
                <div style={{ textAlign: 'center' }}>
                  <Button type="link" onClick={() => history.push(getUrlWithChain('/relayers'))}>
                    {intl.formatMessage({ id: 'pages.welcome.viewAll', defaultMessage: '查看全部' })}
                  </Button>
                </div>
              )}
            />
          </Card>
        </Col>
      </Row>

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

export default Welcome;
