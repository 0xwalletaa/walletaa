import { PageContainer } from '@ant-design/pro-components';
import { useIntl } from '@umijs/max';
import { Card, Col, Row } from 'antd';
import { Pie } from '@ant-design/plots';
import numeral from 'numeral';
import React, { useEffect, useState } from 'react';
import { getComparison, ComparisonData } from '@/services/api';
import { getCurrentChain } from '@/services/config';

const Comparison: React.FC = () => {
  const intl = useIntl();
  const [loading, setLoading] = useState(true);
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
  const currentChain = getCurrentChain();

  // 定义链的显示顺序
  const chainOrder = ['mainnet', 'base', 'arb', 'op', 'sepolia', 'bsc', 'bera', 'gnosis', 'scroll', 'uni', 'ink'];

  // 链名映射：短链名 -> 全名
  const getChainFullName = (chainName: string): string => {
    const chainNameMap: Record<string, string> = {
      'mainnet': intl.formatMessage({ id: 'component.chainSelect.mainnet', defaultMessage: 'Mainnet' }),
      'base': intl.formatMessage({ id: 'component.chainSelect.base', defaultMessage: 'Base' }),
      'arb': intl.formatMessage({ id: 'component.chainSelect.arb', defaultMessage: 'Arbitrum' }),
      'op': intl.formatMessage({ id: 'component.chainSelect.op', defaultMessage: 'Optimism' }),
      'sepolia': intl.formatMessage({ id: 'component.chainSelect.sepolia', defaultMessage: 'Sepolia' }),
      'bsc': intl.formatMessage({ id: 'component.chainSelect.bsc', defaultMessage: 'BSC' }),
      'bera': intl.formatMessage({ id: 'component.chainSelect.bera', defaultMessage: 'Bera' }),
      'gnosis': intl.formatMessage({ id: 'component.chainSelect.gnosis', defaultMessage: 'Gnosis' }),
      'scroll': intl.formatMessage({ id: 'component.chainSelect.scroll', defaultMessage: 'Scroll' }),
      'uni': intl.formatMessage({ id: 'component.chainSelect.uni', defaultMessage: 'Uni' }),
      'ink': intl.formatMessage({ id: 'component.chainSelect.ink', defaultMessage: 'Ink' }),
    };
    return chainNameMap[chainName] || chainName;
  };

  useEffect(() => {
    getComparison()
      .then(data => {
        setComparisonData(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('获取对比数据失败:', error);
        setLoading(false);
      });
  }, []);

  // 准备交易数量饼状图数据
  const getTxCountPieData = () => {
    if (!comparisonData) return [];
    return chainOrder
      .filter(chainName => comparisonData[chainName])
      .map(chainName => ({
        type: getChainFullName(chainName),
        value: comparisonData[chainName].tx_count,
      }))
      .filter(item => item.value > 0);
  };

  // 准备授权者数量饼状图数据
  const getAuthorizerCountPieData = () => {
    if (!comparisonData) return [];
    return chainOrder
      .filter(chainName => comparisonData[chainName])
      .map(chainName => ({
        type: getChainFullName(chainName),
        value: comparisonData[chainName].authorizer_count,
      }))
      .filter(item => item.value > 0);
  };

  // 准备代码数量饼状图数据
  const getCodeCountPieData = () => {
    if (!comparisonData) return [];
    return chainOrder
      .filter(chainName => comparisonData[chainName])
      .map(chainName => ({
        type: getChainFullName(chainName),
        value: comparisonData[chainName].code_count,
      }))
      .filter(item => item.value > 0);
  };

  // 准备中继者数量饼状图数据
  const getRelayerCountPieData = () => {
    if (!comparisonData) return [];
    return chainOrder
      .filter(chainName => comparisonData[chainName])
      .map(chainName => ({
        type: getChainFullName(chainName),
        value: comparisonData[chainName].relayer_count,
      }))
      .filter(item => item.value > 0);
  };

  // 准备TVL饼状图数据
  const getTotalTVLPieData = () => {
    if (!comparisonData) return [];
    return chainOrder
      .filter(chainName => comparisonData[chainName] && chainName !== 'sepolia') // 排除Sepolia链
      .map(chainName => ({
        type: getChainFullName(chainName),
        value: comparisonData[chainName].tvls.total_tvl_balance,
      }))
      .filter(item => item.value > 0);
  };

  // 计算总和的辅助函数
  const calculateTotal = (data: any[]) => {
    return data.reduce((sum, item) => sum + item.value, 0);
  };

  // 通用饼状图配置
  const getPieConfig = (data: any[], title: string, valueFormatter: string = '0,0') => ({
    data,
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    height: 300,
    label: {
      text: (d: any) => {
        // 获取当前链的全名
        const currentChainFullName = getChainFullName(currentChain);
        // 只对当前链显示label
        if (d.type === currentChainFullName) {
          return `${d.type}\n${numeral(d.value).format(valueFormatter)}`;
        }
        return '';
      },
      position: (d: any) => {
        // 获取当前链的全名
        const currentChainFullName = getChainFullName(currentChain);
        // 只对当前链显示label
        if (d.type === currentChainFullName) {
          return 'spider';
        }
        return 'none';
      },
    },
    legend: {
      color: {
        position: 'bottom',
        layout: 'horizontal',
      },
    },
    tooltip: {
      title: (datum: any) => datum.type,
      items: [
        { 
          name: title, 
          channel: 'y', 
          valueFormatter: (value: number) => numeral(value).format(valueFormatter)
        }
      ],
    },
  });

  return (
    <PageContainer title={intl.formatMessage({ id: 'pages.comparison.title', defaultMessage: 'Chain Comparison' })}>
      <Row gutter={[24, 24]}>
        <Col xl={24} lg={24} md={24} sm={24} xs={24}>
          <Card
            bordered={false}
            title={intl.formatMessage({ id: 'pages.comparison.tvlTitle', defaultMessage: 'Total TVL Comparison' })}
            loading={loading}
            style={{ height: '100%' }}
          >
            <div style={{ marginBottom: 20, textAlign: 'center' }}>
              <div style={{ fontSize: '18px', color: 'rgba(0,0,0,.65)', marginBottom: 8 }}>
                Total TVL
              </div>
              <div style={{ fontSize: '30px', lineHeight: '38px', color: 'rgba(0,0,0,.85)', marginBottom: 4 }}>
                ${numeral(calculateTotal(getTotalTVLPieData())).format('0,0.00')}
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'center' }}>
              <div style={{ width: '60%', maxWidth: '600px' }}>
                <Pie {...getPieConfig(getTotalTVLPieData(), 'TVL', '$0,0.00')} />
              </div>
            </div>
          </Card>
        </Col>
        
        <Col xl={12} lg={12} md={24} sm={24} xs={24}>
          <Card
            bordered={false}
            title={intl.formatMessage({ id: 'pages.comparison.txCountTitle', defaultMessage: 'Transaction Count Comparison' })}
            loading={loading}
            style={{ height: '100%' }}
          >
            <div style={{ marginBottom: 20, textAlign: 'center' }}>
              <div style={{ fontSize: '18px', color: 'rgba(0,0,0,.65)', marginBottom: 8 }}>
                Total Transaction Count
              </div>
              <div style={{ fontSize: '30px', lineHeight: '38px', color: 'rgba(0,0,0,.85)', marginBottom: 4 }}>
                {numeral(calculateTotal(getTxCountPieData())).format('0,0')}
              </div>
            </div>
            <Pie {...getPieConfig(getTxCountPieData(), 'Transactions')} />
          </Card>
        </Col>

        <Col xl={12} lg={12} md={24} sm={24} xs={24}>
          <Card
            bordered={false}
            title={intl.formatMessage({ id: 'pages.comparison.authorizerCountTitle', defaultMessage: 'Authorizer Count Comparison' })}
            loading={loading}
            style={{ height: '100%' }}
          >
            <div style={{ marginBottom: 20, textAlign: 'center' }}>
              <div style={{ fontSize: '18px', color: 'rgba(0,0,0,.65)', marginBottom: 8 }}>
                Total Authorizer Count
              </div>
              <div style={{ fontSize: '30px', lineHeight: '38px', color: 'rgba(0,0,0,.85)', marginBottom: 4 }}>
                {numeral(calculateTotal(getAuthorizerCountPieData())).format('0,0')}
              </div>
            </div>
            <Pie {...getPieConfig(getAuthorizerCountPieData(), 'Authorizers')} />
          </Card>
        </Col>

        <Col xl={12} lg={12} md={24} sm={24} xs={24}>
          <Card
            bordered={false}
            title={intl.formatMessage({ id: 'pages.comparison.codeCountTitle', defaultMessage: 'Code Count Comparison' })}
            loading={loading}
            style={{ height: '100%' }}
          >
            <div style={{ marginBottom: 20, textAlign: 'center' }}>
              <div style={{ fontSize: '18px', color: 'rgba(0,0,0,.65)', marginBottom: 8 }}>
                Total Code Count
              </div>
              <div style={{ fontSize: '30px', lineHeight: '38px', color: 'rgba(0,0,0,.85)', marginBottom: 4 }}>
                {numeral(calculateTotal(getCodeCountPieData())).format('0,0')}
              </div>
            </div>
            <Pie {...getPieConfig(getCodeCountPieData(), 'Codes')} />
          </Card>
        </Col>

        <Col xl={12} lg={12} md={24} sm={24} xs={24}>
          <Card
            bordered={false}
            title={intl.formatMessage({ id: 'pages.comparison.relayerCountTitle', defaultMessage: 'Relayer Count Comparison' })}
            loading={loading}
            style={{ height: '100%' }}
          >
            <div style={{ marginBottom: 20, textAlign: 'center' }}>
              <div style={{ fontSize: '18px', color: 'rgba(0,0,0,.65)', marginBottom: 8 }}>
                Total Relayer Count
              </div>
              <div style={{ fontSize: '30px', lineHeight: '38px', color: 'rgba(0,0,0,.85)', marginBottom: 4 }}>
                {numeral(calculateTotal(getRelayerCountPieData())).format('0,0')}
              </div>
            </div>
            <Pie {...getPieConfig(getRelayerCountPieData(), 'Relayers')} />
          </Card>
        </Col>

      </Row>
    </PageContainer>
  );
};

export default Comparison;