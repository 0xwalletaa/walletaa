import React, { useState, useEffect } from 'react';
import { useIntl } from '@umijs/max';
import { Radio, Select } from 'antd';
import { ChainType, CHAIN_CONFIGS, getCurrentChain, DEFAULT_CHAIN } from '@/services/config';
import { history } from '@umijs/max';

/**
 * 链选择器组件
 */
const ChainSelect: React.FC = () => {
  const intl = useIntl();
  const currentChain = getCurrentChain();
  const [isMobile, setIsMobile] = useState(false);

  // 检测屏幕尺寸
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768); // 768px以下认为是移动端
    };

    // 初始检测
    checkMobile();

    // 监听窗口尺寸变化
    window.addEventListener('resize', checkMobile);

    return () => {
      window.removeEventListener('resize', checkMobile);
    };
  }, []);

  // 切换链
  const handleChange = (value: ChainType) => {
    const urlParams = new URLSearchParams(window.location.search);
    
    // 如果切换到默认链，则移除chain参数
    if (value === DEFAULT_CHAIN) {
      urlParams.delete('chain');
    } else {
      urlParams.set('chain', value);
    }
    
    // 构建新的URL
    const newSearch = urlParams.toString();
    const newPath = newSearch ? `${window.location.pathname}?${newSearch}` : window.location.pathname;
    
    history.push(newPath);
    // 重新加载页面以应用新的链配置
    window.location.reload();
  };

  // 选项数据
  const options = [
    { value: 'mainnet', label: intl.formatMessage({ id: 'component.chainSelect.mainnet', defaultMessage: 'Mainnet' }) },
    { value: 'base', label: intl.formatMessage({ id: 'component.chainSelect.base', defaultMessage: 'Base' }) },
    { value: 'op', label: intl.formatMessage({ id: 'component.chainSelect.op', defaultMessage: 'Optimism' }) },
    { value: 'sepolia', label: intl.formatMessage({ id: 'component.chainSelect.sepolia', defaultMessage: 'Sepolia' }) },
    { value: 'bsc', label: intl.formatMessage({ id: 'component.chainSelect.bsc', defaultMessage: 'BSC' }) },
    { value: 'bera', label: intl.formatMessage({ id: 'component.chainSelect.bera', defaultMessage: 'Bera' }) },
    { value: 'gnosis', label: intl.formatMessage({ id: 'component.chainSelect.gnosis', defaultMessage: 'Gnosis' }) },
    { value: 'scroll', label: intl.formatMessage({ id: 'component.chainSelect.scroll', defaultMessage: 'Scroll' }) },
    { value: 'uni', label: intl.formatMessage({ id: 'component.chainSelect.uni', defaultMessage: 'Uni' }) },
    { value: 'ink', label: intl.formatMessage({ id: 'component.chainSelect.ink', defaultMessage: 'Ink' }) },
  ];

  // 移动端渲染下拉框
  if (isMobile) {
    return (
      <Select
        value={currentChain}
        onChange={handleChange}
        options={options}
        size="large"
        style={{ marginRight: 12, width: 120 }}
      />
    );
  }

  // 桌面端渲染单选框
  return (
    <Radio.Group
      value={currentChain}
      onChange={(e) => handleChange(e.target.value)}
      buttonStyle="solid"
      style={{ marginRight: 12 }}
    >
      {options.map(option => (
        <Radio.Button key={option.value} value={option.value}>
          {option.label}
        </Radio.Button>
      ))}
    </Radio.Group>
  );
};

export default ChainSelect; 