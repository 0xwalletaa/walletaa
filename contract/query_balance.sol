// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
}

contract BalanceQuery {
    address public constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address public constant WBTC = 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599;
    address public constant USDT = 0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address public constant USDC = 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48;
    address public constant DAI = 0x6B175474E89094C44Da98b954EedeAC495271d0F;

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
