import { GithubOutlined, TwitterOutlined, MessageOutlined } from '@ant-design/icons';
import { DefaultFooter } from '@ant-design/pro-components';
import React from 'react';

const Footer: React.FC = () => {
  return (
    <DefaultFooter
      style={{
        background: 'none',
        paddingBottom: 0,
      }}
      copyright={false}
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
        {
          key: 'donation',
          title: (
            <div style={{ marginTop: '8px', color: 'rgba(0, 0, 0, 0.45)', fontSize: '14px' }}>
              <div>Donations are greatly appreciated!</div>
              <div>
                ETH:{' '}
                <a
                  href="https://etherscan.io/address/0x8EA35dd88e2e7ec04a3C5F9B36Bd9eda90424a32"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ color: '#1890ff' }}
                >
                  0x8EA35dd88e2e7ec04a3C5F9B36Bd9eda90424a32
                </a>
              </div>
            </div>
          ),
          href: '',
          blankTarget: false,
        },
      ]}
    />
  );
};

export default Footer;
