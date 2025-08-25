import { PageContainer } from '@ant-design/pro-components';
import { useIntl } from '@umijs/max';
import { Card, Col, Row, Spin } from 'antd';
import { Pie, Bar } from '@ant-design/plots';
import numeral from 'numeral';
import React, { useEffect, useState } from 'react';
import { getCodeStatistics, CodeStatistics } from '@/services/api';

const Statistics: React.FC = () => {
  const intl = useIntl();
  const [loading, setLoading] = useState(true);
  const [statistics, setStatistics] = useState<CodeStatistics | null>(null);

  useEffect(() => {
    getCodeStatistics()
      .then(data => {
        setStatistics(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('获取统计数据失败:', error);
        setLoading(false);
      });
  }, []);

  // 准备Type的饼状图数据
  const getTypeCountPieData = () => {
    if (!statistics || !statistics.code_count_by_type) return [];
    return Object.entries(statistics.code_count_by_type).map(([type, count]) => ({
      type,
      value: count,
    }));
  };

  const getTypeAuthorizerPieData = () => {
    if (!statistics || !statistics.code_authorizer_by_type) return [];
    return Object.entries(statistics.code_authorizer_by_type).map(([type, count]) => ({
      type,
      value: count,
    }));
  };

  const getTypeTvlPieData = () => {
    if (!statistics || !statistics.code_tvl_by_type) return [];
    return Object.entries(statistics.code_tvl_by_type).map(([type, tvl]) => ({
      type,
      value: tvl,
    }));
  };

  // 准备Tag的水平柱状图数据
  const getTagCountBarData = () => {
    if (!statistics || !statistics.code_count_by_tag) return [];
    return Object.entries(statistics.code_count_by_tag)
      .map(([tag, count]) => ({
        tag,
        value: count,
      }))
      .sort((a, b) => b.value - a.value);
  };

  const getTagAuthorizerBarData = () => {
    if (!statistics || !statistics.code_authorizer_by_tag) return [];
    return Object.entries(statistics.code_authorizer_by_tag)
      .map(([tag, count]) => ({
        tag,
        value: count,
      }))
      .sort((a, b) => b.value - a.value);
  };

  const getTagTvlBarData = () => {
    if (!statistics || !statistics.code_tvl_by_tag) return [];
    return Object.entries(statistics.code_tvl_by_tag)
      .map(([tag, tvl]) => ({
        tag,
        value: tvl,
      }))
      .sort((a, b) => b.value - a.value);
  };

  return (
    <PageContainer title={intl.formatMessage({ id: 'pages.statistics.title' })}>
      <Spin spinning={loading}>
        {/* Type 分布图 - 第一行 */}
        <Row gutter={24} style={{ marginBottom: 24 }}>
          <Col xl={8} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
            <Card
              bordered={false}
              title={intl.formatMessage({ id: 'pages.statistics.tvlByType' })}
              style={{ height: '100%' }}
            >
              <Pie
                data={getTypeTvlPieData()}
                angleField="value"
                colorField="type"
                radius={0.8}
                height={200}
                label={{
                  type: 'inner',
                  offset: '-30%',
                  content: ({ percent }: any) => `${(percent * 100).toFixed(1)}%`,
                  style: {
                    fontSize: 12,
                    textAlign: 'center',
                  },
                }}
                legend={{
                  color: {
                    position: 'right',
                    layout: 'vertical',
                  },
                }}
                tooltip={{
                  items: [{ name: 'TVL', field: 'value', valueFormatter: (value) => `$${numeral(value).format('0,0.00')}` }],
                }}
              />
            </Card>
          </Col>
          <Col xl={8} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
            <Card
              bordered={false}
              title={intl.formatMessage({ id: 'pages.statistics.authorizerCountByType' })}
              style={{ height: '100%' }}
            >
              <Pie
                data={getTypeAuthorizerPieData()}
                angleField="value"
                colorField="type"
                radius={0.8}
                height={200}
                label={{
                  type: 'inner',
                  offset: '-30%',
                  content: ({ percent }: any) => `${(percent * 100).toFixed(1)}%`,
                  style: {
                    fontSize: 12,
                    textAlign: 'center',
                  },
                }}
                legend={{
                  color: {
                    position: 'right',
                    layout: 'vertical',
                  },
                }}
                tooltip={{
                  items: [{ name: intl.formatMessage({ id: 'pages.statistics.authorizers' }), field: 'value' }],
                }}
              />
            </Card>
          </Col>
          <Col xl={8} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
            <Card
              bordered={false}
              title={intl.formatMessage({ id: 'pages.statistics.codeCountByType' })}
              style={{ height: '100%' }}
            >
              <Pie
                data={getTypeCountPieData()}
                angleField="value"
                colorField="type"
                radius={0.8}
                height={200}
                label={{
                  type: 'inner',
                  offset: '-30%',
                  content: ({ percent }: any) => `${(percent * 100).toFixed(1)}%`,
                  style: {
                    fontSize: 12,
                    textAlign: 'center',
                  },
                }}
                legend={{
                  color: {
                    position: 'right',
                    layout: 'vertical',
                  },
                }}
                tooltip={{
                  items: [{ name: intl.formatMessage({ id: 'pages.statistics.count' }), field: 'value' }],
                }}
              />
            </Card>
          </Col>
        </Row>

        {/* Tag 分布图 - 第二行 */}
        <Row gutter={24}>
          <Col xl={8} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
            <Card
              bordered={false}
              title={intl.formatMessage({ id: 'pages.statistics.tvlByTag' })}
              style={{ height: '100%' }}
            >
              <Bar
                data={getTagTvlBarData()}
                xField="tag"
                yField="value"
                colorField="tag"
                height={400}
                legend={false}
                axis={{
                  y: {
                    title: false,
                  },
                  x: {
                    title: false,
                    label: {
                      rotate: Math.PI / 4,
                      style: {
                        fontSize: 12,
                      },
                    },
                  },
                }}
                tooltip={{
                  items: [{ name: 'TVL', field: 'value', valueFormatter: (value) => `$${numeral(value).format('0,0.00')}` }],
                }}
                state={{
                  unselected: { opacity: 0.5 },
                  selected: { lineWidth: 3, stroke: '#1890ff' },
                }}
                interaction={{
                  elementSelect: true,
                }}
              />
            </Card>
          </Col>
          <Col xl={8} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
            <Card
              bordered={false}
              title={intl.formatMessage({ id: 'pages.statistics.authorizerCountByTag' })}
              style={{ height: '100%' }}
            >
              <Bar
                data={getTagAuthorizerBarData()}
                xField="tag"
                yField="value"
                colorField="tag"
                height={400}
                legend={false}
                axis={{
                  y: {
                    title: false,
                  },
                  x: {
                    title: false,
                    label: {
                      rotate: Math.PI / 4,
                      style: {
                        fontSize: 12,
                      },
                    },
                  },
                }}
                tooltip={{
                  items: [{ name: intl.formatMessage({ id: 'pages.statistics.authorizers' }), field: 'value' }],
                }}
                state={{
                  unselected: { opacity: 0.5 },
                  selected: { lineWidth: 3, stroke: '#1890ff' },
                }}
                interaction={{
                  elementSelect: true,
                }}
              />
            </Card>
          </Col>
          <Col xl={8} lg={24} md={24} sm={24} xs={24} style={{ marginBottom: 24 }}>
            <Card
              bordered={false}
              title={intl.formatMessage({ id: 'pages.statistics.codeCountByTag' })}
              style={{ height: '100%' }}
            >
              <Bar
                data={getTagCountBarData()}
                xField="tag"
                yField="value"
                colorField="tag"
                height={400}
                legend={false}
                axis={{
                  y: {
                    title: false,
                  },
                  x: {
                    title: false,
                    label: {
                      rotate: Math.PI / 4,
                      style: {
                        fontSize: 12,
                      },
                    },
                  },
                }}
                tooltip={{
                  items: [{ name: intl.formatMessage({ id: 'pages.statistics.count' }), field: 'value' }],
                }}
                state={{
                  unselected: { opacity: 0.5 },
                  selected: { lineWidth: 3, stroke: '#1890ff' },
                }}
                interaction={{
                  elementSelect: true,
                }}
              />
            </Card>
          </Col>
        </Row>
      </Spin>
    </PageContainer>
  );
};

export default Statistics;
