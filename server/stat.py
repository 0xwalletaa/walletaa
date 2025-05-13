import util

util.NAME = "mainnet"

txs = util.get_all_type4_txs()

print(len(txs))