import React from 'react';
import { useIntl } from '@umijs/max';
import { Select } from 'antd';
import { ChainType, CHAIN_CONFIGS, getCurrentChain, DEFAULT_CHAIN } from '@/services/config';
import { history } from '@umijs/max';

/**
 * 链选择器组件
 */
const ChainSelect: React.FC = () => {
  const intl = useIntl();
  const currentChain = getCurrentChain();

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

  return (
    <Select
      value={currentChain}
      onChange={handleChange}
      options={[
        { value: 'mainnet', label: intl.formatMessage({ id: 'component.chainSelect.mainnet', defaultMessage: 'Mainnet' }) },
        { value: 'sepolia', label: intl.formatMessage({ id: 'component.chainSelect.sepolia', defaultMessage: 'Sepolia' }) },
      ]}
      style={{ marginRight: 12, width: 120 }}
    />
  );
};

export default ChainSelect; 