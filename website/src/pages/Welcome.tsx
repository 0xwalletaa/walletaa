import { InfoCircleOutlined } from '@ant-design/icons';
import { PageContainer } from '@ant-design/pro-components';
import { useRequest } from '@umijs/max';
import { Card, Col, Row, Table, Tooltip } from 'antd';
import { Area, Column } from '@ant-design/plots';
import numeral from 'numeral';
import React, { useEffect, useState, ReactNode } from 'react';

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

// 定义Overview类型
interface Overview {
  tx_count: number;
  authorizer_count: number;
  code_count: number;
  relayer_count: number;
  daily_tx_count: Record<string, number>;
  daily_cumulative_tx_count: Record<string, number>;
  daily_authorizaion_count: Record<string, number>;
  daily_cumulative_authorizaion_count: Record<string, number>;
  top10_codes: Array<{
    code_address: string;
    authorizer_count: number;
    eth_balance: number;
  }>;
  top10_relayers: Array<{
    relayer_address: string;
    tx_count: number;
    authorization_count: number;
    tx_fee: number;
  }>;
}

// 定义图表数据类型
interface ChartDataItem {
  x: string;
  y: number;
}

// 引入ChartCard和Field组件
const ChartCard: React.FC<ChartCardProps> = ({ loading, title, total, contentHeight = 46, footer, children, bordered = true }) => {
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
            <Tooltip title="数据说明">
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
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<Overview | null>(null);

  useEffect(() => {
    fetch('https://walletaa.com/api-sepolia/overview')
      .then(response => response.json())
      .then(data => {
        setOverview(data.overview);
        setLoading(false);
      })
      .catch(error => {
        console.error('获取数据失败:', error);
        setLoading(false);
      });
  }, []);

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

  const codeRankColumns = [
    {
      title: '排名',
      dataIndex: 'index',
      key: 'index',
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: '代码地址',
      dataIndex: 'code_address',
      key: 'code_address',
      render: (text: string) => <a href={`https://sepolia.etherscan.io/address/${text}`} target="_blank" rel="noopener noreferrer">{text}</a>,
    },
    {
      title: '授权者数量',
      dataIndex: 'authorizer_count',
      key: 'authorizer_count',
      sorter: (a: any, b: any) => a.authorizer_count - b.authorizer_count,
    },
    {
      title: 'ETH余额',
      dataIndex: 'eth_balance',
      key: 'eth_balance',
      sorter: (a: any, b: any) => a.eth_balance - b.eth_balance,
      render: (text: number) => numeral(text).format('0,0.0000'),
    },
  ];

  const relayerRankColumns = [
    {
      title: '排名',
      dataIndex: 'index',
      key: 'index',
      render: (_: any, __: any, index: number) => index + 1,
    },
    {
      title: '中继者地址',
      dataIndex: 'relayer_address',
      key: 'relayer_address',
      render: (text: string) => <a href={`https://sepolia.etherscan.io/address/${text}`} target="_blank" rel="noopener noreferrer">{text}</a>,
    },
    {
      title: '交易数量',
      dataIndex: 'tx_count',
      key: 'tx_count',
      sorter: (a: any, b: any) => a.tx_count - b.tx_count,
    },
    {
      title: '授权数量',
      dataIndex: 'authorization_count',
      key: 'authorization_count',
      sorter: (a: any, b: any) => a.authorization_count - b.authorization_count,
    },
    {
      title: '交易费用(ETH)',
      dataIndex: 'tx_fee',
      key: 'tx_fee',
      sorter: (a: any, b: any) => a.tx_fee - b.tx_fee,
      render: (text: number) => numeral(text).format('0,0.0000'),
    },
  ];

  return (
    <PageContainer>
      <Row gutter={24}>
        <Col {...topColResponsiveProps}>
          <ChartCard
            bordered={false}
            title="交易数量"
            loading={loading}
            total={overview ? numeral(overview.tx_count).format('0,0') : 0}
            footer={<Field label="总交易数" value={overview ? numeral(overview.tx_count).format('0,0') : 0} />}
            contentHeight={46}
          >
            <Area
              xField="x"
              yField="y"
              shapeField="smooth"
              height={46}
              axis={false}
              style={{
                fill: 'linear-gradient(-90deg, white 0%, #975FE4 100%)',
                fillOpacity: 0.6,
                width: '100%',
              }}
              padding={-20}
              data={getCumulativeTxData()}
            />
          </ChartCard>
        </Col>

        <Col {...topColResponsiveProps}>
          <ChartCard
            bordered={false}
            loading={loading}
            title="授权者数量"
            total={overview ? numeral(overview.authorizer_count).format('0,0') : 0}
            footer={<Field label="总授权者数" value={overview ? numeral(overview.authorizer_count).format('0,0') : 0} />}
            contentHeight={46}
          >
            <Area
              xField="x"
              yField="y"
              shapeField="smooth"
              height={46}
              axis={false}
              style={{
                fill: 'linear-gradient(-90deg, white 0%, #975FE4 100%)',
                fillOpacity: 0.6,
                width: '100%',
              }}
              padding={-20}
              data={getCumulativeAuthData()}
            />
          </ChartCard>
        </Col>

        <Col {...topColResponsiveProps}>
          <ChartCard
            bordered={false}
            loading={loading}
            title="代码数量"
            total={overview ? numeral(overview.code_count).format('0,0') : 0}
            footer={<Field label="总代码数" value={overview ? numeral(overview.code_count).format('0,0') : 0} />}
            contentHeight={46}
          >
            <Column
              xField="x"
              yField="y"
              padding={-20}
              axis={false}
              height={46}
              data={[]}
              scale={{ x: { paddingInner: 0.4 } }}
            />
          </ChartCard>
        </Col>

        <Col {...topColResponsiveProps}>
          <ChartCard
            loading={loading}
            bordered={false}
            title="中继者数量"
            total={overview ? numeral(overview.relayer_count).format('0,0') : 0}
            footer={<Field label="总中继者数" value={overview ? numeral(overview.relayer_count).format('0,0') : 0} />}
            contentHeight={46}
          >
            <Column
              xField="x"
              yField="y"
              padding={-20}
              axis={false}
              height={46}
              data={[]}
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
                <h4 style={{ marginBottom: 20 }}>每日交易量</h4>
                <Column
                  height={400}
                  data={getDailyTxCountData()}
                  xField="x"
                  yField="y"
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
                  scale={{
                    x: { paddingInner: 0.4 },
                  }}
                  tooltip={{
                    name: '交易数量',
                    channel: 'y',
                  }}
                />
              </div>
            </Col>
            <Col xl={12} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
              <div style={{ position: 'relative' }}>
                <h4 style={{ marginBottom: 20 }}>每日授权量</h4>
                <Column
                  height={400}
                  data={getDailyAuthCountData()}
                  xField="x"
                  yField="y"
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
                  scale={{
                    x: { paddingInner: 0.4 },
                  }}
                  tooltip={{
                    name: '授权数量',
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
            title="代码排行榜"
            loading={loading}
            style={{ height: '100%' }}
            bodyStyle={{ padding: '0 24px 24px 24px' }}
          >
            <Table
              rowKey="code_address"
              size="small"
              columns={codeRankColumns}
              dataSource={overview ? overview.top10_codes : []}
              pagination={false}
            />
          </Card>
        </Col>
        <Col xl={12} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
          <Card
            bordered={false}
            title="中继者排行榜"
            loading={loading}
            style={{ height: '100%' }}
            bodyStyle={{ padding: '0 24px 24px 24px' }}
          >
            <Table
              rowKey="relayer_address"
              size="small"
              columns={relayerRankColumns}
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
