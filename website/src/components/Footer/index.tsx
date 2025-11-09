import { GithubOutlined, TwitterOutlined, MessageOutlined } from '@ant-design/icons';
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
          key: 'github',
          title: (
            <>
              <GithubOutlined /> Github
            </>
          ),
          href: 'https://github.com/0xwalletaa/walletaa',
          blankTarget: true,
        },
        {
          key: 'x',
          title: (
            <>
              <TwitterOutlined /> X
            </>
          ),
          href: 'https://twitter.com/wallet_aa',
          blankTarget: true,
        },
        {
          key: 'telegram',
          title: (
            <>
              <MessageOutlined /> Telegram
            </>
          ),
          href: 'https://t.me/+BrxklVaUBnRhOWIx',
          blankTarget: true,
        },
      ]}
    />
  );
};

export default Footer;
