// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function balanceOf(address account) external view returns (uint256);
}

contract BalanceQuery {
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
        }
        
        return balances;
    }
}
