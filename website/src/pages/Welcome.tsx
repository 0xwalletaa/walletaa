import { InfoCircleOutlined } from '@ant-design/icons';
import { PageContainer } from '@ant-design/pro-components';
import { useIntl } from '@umijs/max';
import { Card, Col, Row, Table, Tooltip, Tag } from 'antd';
import { Area, Column } from '@ant-design/plots';
import numeral from 'numeral';
import React, { useEffect, useState, ReactNode } from 'react';
import { getOverview, Overview } from '@/services/api';

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

  useEffect(() => {
    getOverview()
      .then(data => {
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

  return (
    <PageContainer>
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
        <Col xl={12} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
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
                    <Tooltip title={text}>
                      <a href={`https://sepolia.etherscan.io/address/${text}`} target="_blank" rel="noopener noreferrer">
                        <Tag color="blue">{formatAddress(text)}</Tag>
                      </a>
                    </Tooltip>
                  ),
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.authorizerCount' }),
                  dataIndex: 'authorizer_count',
                  key: 'authorizer_count',
                },
                {
                  title: intl.formatMessage({ id: 'pages.welcome.ethBalance' }),
                  dataIndex: 'eth_balance',
                  key: 'eth_balance',
                  render: (text: number) => numeral(text).format('0,0.0000'),
                },
              ]}
              dataSource={overview ? overview.top10_codes : []}
              pagination={false}
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
                    <Tooltip title={text}>
                      <a href={`https://sepolia.etherscan.io/address/${text}`} target="_blank" rel="noopener noreferrer">
                        <Tag color="purple">{formatAddress(text)}</Tag>
                      </a>
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
                  title: intl.formatMessage({ id: 'pages.welcome.txFee' }),
                  dataIndex: 'tx_fee',
                  key: 'tx_fee',
                  render: (text: number) => numeral(text).format('0,0.0000'),
                },
              ]}
              dataSource={overview ? overview.top10_relayers : []}
              pagination={false}
            />
          </Card>
        </Col>
      </Row>
    </PageContainer>
  );
};

export default Welcome;
