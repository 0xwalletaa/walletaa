// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
}

contract BalanceQuery {
    address public constant WETH = 0x4200000000000000000000000000000000000006;
    address public constant WBTC = 0x0555e30da8f98308edb960aa94c0db47230d2b9c;
    address public constant USDT = 0xfde4c96c8593536e31f229ea8f37b2ada2699bb2;
    address public constant USDC = 0x833589fcd6edb6e08f4c7c32d4f71b54bda02913;
    address public constant DAI = 0x50c5725949a6f0c72e6c4a641f24049a917db0cb;

    struct TokenBalances {
        uint256 ethBalance;
        uint256 wethBalance;
        uint256 wbtcBalance;
        uint256 usdtBalance;
        uint256 usdcBalance;
        uint256 daiBalance;
    }

    function get(address target) public view returns (TokenBalances memory) {
        TokenBalances memory balances;
        
        // 获取ETH余额
        balances.ethBalance = target.balance;
        
        // 获取各ERC20代币余额
        balances.wethBalance = IERC20(WETH).balanceOf(target);
        balances.wbtcBalance = IERC20(WBTC).balanceOf(target);
        balances.usdtBalance = IERC20(USDT).balanceOf(target);
        balances.usdcBalance = IERC20(USDC).balanceOf(target);
        balances.daiBalance = IERC20(DAI).balanceOf(target);
        
        return balances;
    }
}
