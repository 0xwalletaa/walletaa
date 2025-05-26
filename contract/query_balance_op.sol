// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
}

contract BalanceQuery {
    address public constant WETH = 0x4200000000000000000000000000000000000006;
    address public constant WBTC = 0x68f180fcCe6836688e9084f035309E29Bf0A2095;
    address public constant USDT = 0x94b008aA00579c1307B0EF2c499aD98a8ce58e58;
    address public constant USDC = 0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85;
    address public constant DAI = 0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1;

    struct TokenBalances {
        uint256 ethBalance;
        uint256 wethBalance;
        uint256 wbtcBalance;
        uint256 usdtBalance;
        uint256 usdcBalance;
        uint256 daiBalance;
    }

    function get(address[] memory targets) public view returns (TokenBalances[] memory) {
        TokenBalances[] memory balances = new TokenBalances[](targets.length);
        
        for (uint256 i = 0; i < targets.length; i++) {
            // 获取ETH余额
            balances[i].ethBalance = targets[i].balance;
        
            // 获取各ERC20代币余额
            balances[i].wethBalance = IERC20(WETH).balanceOf(targets[i]);
            balances[i].wbtcBalance = IERC20(WBTC).balanceOf(targets[i]);
            balances[i].usdtBalance = IERC20(USDT).balanceOf(targets[i]);
            balances[i].usdcBalance = IERC20(USDC).balanceOf(targets[i]);
            balances[i].daiBalance = IERC20(DAI).balanceOf(targets[i]);
        }
        
        return balances;
    }
}
