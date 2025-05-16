import util
import time

util.NAME = "mainnet"

start_time = time.time()

txs = util.get_all_type4_txs()

print(len(txs))

end_time = time.time()
print(f"Time taken: {end_time - start_time} seconds")