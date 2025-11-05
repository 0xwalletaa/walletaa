export DB_PATH=$DB_PATH
export NAME=arb
python3 updater_mysql.py --no-tvl --no-code
python3 cache_overview.py
export NAME=base
python3 updater_mysql.py --no-tvl --no-code
python3 cache_overview.py
export NAME=bera
python3 updater_mysql.py --no-tvl --no-code
python3 cache_overview.py
export NAME=bsc
python3 updater_mysql.py --no-tvl --no-code
python3 cache_overview.py
export NAME=gnosis
python3 updater_mysql.py --no-tvl --no-code
python3 cache_overview.py
export NAME=ink
python3 updater_mysql.py --no-tvl --no-code
python3 cache_overview.py
export NAME=mainnet
python3 updater_mysql.py --no-tvl --no-code
python3 cache_overview.py
export NAME=op
python3 updater_mysql.py --no-tvl --no-code
python3 cache_overview.py
export NAME=scroll
python3 updater_mysql.py --no-tvl --no-code
python3 cache_overview.py
export NAME=uni
python3 updater_mysql.py --no-tvl --no-code
python3 cache_overview.py