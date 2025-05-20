// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
}

contract BalanceQuery {
    address public constant WETH = 0x2170Ed0880ac9A755fd29B2688956BD959F933F8;
    address public constant WBTC = 0x0555E30da8f98308EdB960aa94C0Db47230d2B9c;
    address public constant USDT = 0x55d398326f99059fF775485246999027B3197955;
    address public constant USDC = 0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d;
    address public constant DAI = 0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3;

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
