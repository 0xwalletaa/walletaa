while true; do
    export NAME=mainnet
    python3 updater_sqlite.py
    export NAME=arb
    python3 updater_sqlite.py
    export NAME=sepolia
    python3 updater_sqlite.py
    export NAME=base
    python3 updater_sqlite.py
    export NAME=bsc
    python3 updater_sqlite.py
    export NAME=op
    python3 updater_sqlite.py
    export NAME=bera
    python3 updater_sqlite.py
    export NAME=gnosis
    python3 updater_sqlite.py
    export NAME=ink
    python3 updater_sqlite.py
    export NAME=uni
    python3 updater_sqlite.py
    export NAME=scroll
    python3 updater_sqlite.py
    sleep 120
done