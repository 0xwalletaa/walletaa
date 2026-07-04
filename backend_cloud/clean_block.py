#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""块库轮换瘦身。

条件: 块库文件超过 --max_size_gb 且存在本地上报的确认文件 {name}_confirmed_*
(该高度以下的块本地已全部下载+解析+验证, 云端不再需要留底)。

做法: 新建带表结构的新库, 把确认高度之后的 blocks / type4_transactions
复制过去, 然后原子替换旧库 (os.replace, 路径始终存在, syncer_server 正在
读旧库的请求顺着已打开的 fd 正常完成), 最后把水位退到确认高度。
没有 DELETE 没有 VACUUM, 旧库整个文件 unlink, IO 只花在复制小尾巴上。

放在 get_{name}.sh 串行末尾执行, 那是这条链抓块进程的安静点。
"""

import os
import sys
import glob
import sqlite3
import argparse
import watermark

parser = argparse.ArgumentParser(description='Rotate block db: drop confirmed history')
parser.add_argument('--name', required=True, help='Blockchain network name')
parser.add_argument('--block_db_path', type=str, default='', help='block_db_path')
parser.add_argument('--max_size_gb', type=float, default=5.0,
                    help='Rotate only when db file exceeds this size (GB)')
args = parser.parse_args()

NAME = args.name

block_db_path = f'{NAME}_block.db'
if args.block_db_path != '':
    block_db_path = f'{args.block_db_path}/{NAME}_block.db'
block_db_path = os.path.abspath(block_db_path)
db_dir = os.path.dirname(block_db_path)


def create_schema(conn):
    """和 get_block_batch.py 的 init_db 保持一致"""
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blocks (
        block_number INTEGER PRIMARY KEY,
        tx_count INTEGER,
        type4_tx_count INTEGER,
        timestamp INTEGER
    )
    ''')
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_blocks_block_number
    ON blocks(block_number ASC);
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS type4_transactions (
        tx_hash TEXT PRIMARY KEY,
        block_number INTEGER,
        tx_data TEXT,
        FOREIGN KEY (block_number) REFERENCES blocks(block_number)
    )
    ''')
    cursor.execute('''
    CREATE INDEX IF NOT EXISTS idx_type4_transactions_block_number
    ON type4_transactions(block_number ASC);
    ''')
    conn.commit()


def main():
    # 清理上次可能残留的半成品
    for stale in glob.glob(block_db_path + '.rotate.*'):
        try:
            os.remove(stale)
            print(f"Removed stale temp file: {stale}")
        except OSError:
            pass

    if not os.path.exists(block_db_path):
        print(f"[clean_block] {NAME}: db not found, skip")
        return

    size = os.path.getsize(block_db_path)
    size_gb = size / 1024 / 1024 / 1024
    if size_gb <= args.max_size_gb:
        print(f"[clean_block] {NAME}: db {size_gb:.2f} GB <= {args.max_size_gb} GB, skip")
        return

    confirmed = watermark.read_confirmed(db_dir, NAME)
    if confirmed is None:
        print(f"[clean_block] {NAME}: db {size_gb:.2f} GB but no confirmed file, skip")
        return

    # 防抖: 如果确认高度太旧, 要保留的尾巴占大头, 轮换释放不了多少空间,
    # 反而每轮重写一遍大文件。保留行数占比超过一半就先不动, 等确认追上来。
    old_conn = sqlite3.connect(block_db_path)
    old_cursor = old_conn.cursor()
    old_cursor.execute("SELECT COUNT(*) FROM blocks WHERE block_number > ?", (confirmed,))
    keep_blocks = old_cursor.fetchone()[0]
    old_cursor.execute("SELECT COUNT(*) FROM blocks")
    total_blocks = old_cursor.fetchone()[0]
    old_conn.close()

    if total_blocks == 0:
        print(f"[clean_block] {NAME}: empty blocks table, skip")
        return
    if keep_blocks * 2 > total_blocks:
        print(f"[clean_block] {NAME}: would keep {keep_blocks}/{total_blocks} rows "
              f"(confirmed={confirmed} too far behind), skip")
        return

    print(f"[clean_block] {NAME}: rotating db {size_gb:.2f} GB, "
          f"keeping {keep_blocks}/{total_blocks} blocks after {confirmed}")

    new_path = f'{block_db_path}.rotate.{os.getpid()}'
    new_conn = sqlite3.connect(new_path)
    try:
        # 复制期间不需要崩溃安全: 半成品下次启动会被清理, 换来复制速度
        new_conn.execute("PRAGMA journal_mode=OFF")
        new_conn.execute("PRAGMA synchronous=OFF")
        create_schema(new_conn)

        new_conn.execute("ATTACH DATABASE ? AS src", (block_db_path,))
        new_conn.execute(
            "INSERT INTO blocks (block_number, tx_count, type4_tx_count, timestamp) "
            "SELECT block_number, tx_count, type4_tx_count, timestamp "
            "FROM src.blocks WHERE block_number > ?", (confirmed,))
        new_conn.execute(
            "INSERT INTO type4_transactions (tx_hash, block_number, tx_data) "
            "SELECT tx_hash, block_number, tx_data "
            "FROM src.type4_transactions WHERE block_number > ?", (confirmed,))
        new_conn.commit()

        copied_blocks = new_conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
        copied_txs = new_conn.execute("SELECT COUNT(*) FROM type4_transactions").fetchone()[0]
        new_conn.execute("DETACH DATABASE src")
    except Exception as e:
        new_conn.close()
        try:
            os.remove(new_path)
        except OSError:
            pass
        print(f"[clean_block] {NAME}: rotation failed, old db untouched: {e}")
        sys.exit(1)
    new_conn.close()

    # 原子替换: 路径上始终有一个完整可用的库
    os.replace(new_path, block_db_path)

    # 清理旧库可能遗留的日志文件, 避免孤儿热日志被配到新库上
    for suffix in ('-journal', '-wal', '-shm'):
        stale = block_db_path + suffix
        if os.path.exists(stale):
            try:
                os.remove(stale)
                print(f"Removed stale journal: {stale}")
            except OSError:
                pass

    # 水位退到确认高度: 下一轮扫描会走一遍 (confirmed, head] 的存在性检查,
    # 复制过来的块都在, 水位自动爬回去, 顺带验证了这次复制
    watermark.rollback_watermark(db_dir, NAME, confirmed)

    new_size = os.path.getsize(block_db_path)
    print(f"[clean_block] {NAME}: done. {size_gb:.2f} GB -> "
          f"{new_size / 1024 / 1024:.1f} MB, "
          f"copied {copied_blocks} blocks / {copied_txs} type4 txs, "
          f"freed {(size - new_size) / 1024 / 1024 / 1024:.2f} GB")


if __name__ == '__main__':
    main()
