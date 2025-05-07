import React from 'react';
import { Link } from '@umijs/max';
import { getCurrentChain, DEFAULT_CHAIN } from '@/services/config';

interface ChainLinkProps {
  to: string;
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * 链接组件，自动在链接中添加当前chain参数
 * 当chain为默认值时不添加参数
 */
const ChainLink: React.FC<ChainLinkProps> = ({ to, children, ...restProps }) => {
  const currentChain = getCurrentChain();
  
  // 如果是默认链，不添加参数
  if (currentChain === DEFAULT_CHAIN) {
    return (
      <Link to={to} {...restProps}>
        {children}
      </Link>
    );
  }
  
  // 非默认链，添加参数
  const path = `${to}${to.includes('?') ? '&' : '?'}chain=${currentChain}`;
  
  return (
    <Link to={path} {...restProps}>
      {children}
    </Link>
  );
};

export default ChainLink; 