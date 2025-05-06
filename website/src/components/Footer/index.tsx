import { GithubOutlined } from '@ant-design/icons';
import { DefaultFooter } from '@ant-design/pro-components';
import React from 'react';

const Footer: React.FC = () => {
  return (
    <DefaultFooter
      style={{
        background: 'none',
      }}
      links={[
        {
          key: 'WalletAA',
          title: 'WalletAA',
          href: 'https://walletaa.com',
          blankTarget: true,
        },
        {
          key: 'github',
          title: <GithubOutlined />,
          href: 'https://github.com/0xwalletaa/',
          blankTarget: true,
        },
        {
          key: '0xWalletAA',
          title: '0xWalletAA',
          href: 'https://github.com/0xwalletaa/',
          blankTarget: true,
        },
      ]}
    />
  );
};

export default Footer;
