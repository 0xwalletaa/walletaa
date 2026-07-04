#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""块同步水位线 (watermark)。

用空文件 `{name}_good_{block}` 记录 "从起始块到 block 已连续无缺口"。
启动时读它就能跳过前面的全量遍历, 直接从 block+1 开始扫描。

wrong_block 流程删块时必须调用 rollback_watermark 把水位线退回删除点
之前, 否则被删的块会被永远跳过。
"""

import os
import re
import glob


def _files(db_dir, name):
    """返回 (path, block) 列表"""
    result = []
    for path in glob.glob(os.path.join(db_dir, f'{name}_good_*')):
        m = re.match(rf'{re.escape(name)}_good_(\d+)$', os.path.basename(path))
        if m:
            result.append((path, int(m.group(1))))
    return result


def read_watermark(db_dir, name):
    """读取水位线, 没有则返回 None。有多个文件时取最大 (多进程竞争的残留)"""
    files = _files(db_dir, name)
    if not files:
        return None
    return max(block for _, block in files)


def write_watermark(db_dir, name, block):
    """推进水位线到 block (只前进不后退), 并清理旧文件"""
    if block is None:
        return
    current = read_watermark(db_dir, name)
    if current is not None and block <= current:
        return
    new_path = os.path.join(db_dir, f'{name}_good_{block}')
    open(new_path, 'w').close()  # 先建新的再删旧的, 中途挂了也不丢水位线
    for path, old_block in _files(db_dir, name):
        if path != new_path:
            try:
                os.remove(path)
            except OSError:
                pass
    print(f"[watermark] {name}: advanced to {block}")


def _confirmed_files(db_dir, name):
    """返回 (path, block) 列表: {name}_confirmed_* 确认文件"""
    result = []
    for path in glob.glob(os.path.join(db_dir, f'{name}_confirmed_*')):
        m = re.match(rf'{re.escape(name)}_confirmed_(\d+)$', os.path.basename(path))
        if m:
            result.append((path, int(m.group(1))))
    return result


def read_confirmed(db_dir, name):
    """读确认高度 (本地已下载+解析+验证完毕的高度), 没有返回 None"""
    files = _confirmed_files(db_dir, name)
    if not files:
        return None
    return max(block for _, block in files)


def write_confirmed(db_dir, name, block):
    """推进确认高度 (只前进不后退), 清理旧文件。返回当前生效的确认高度。"""
    current = read_confirmed(db_dir, name)
    if current is not None and block <= current:
        return current
    new_path = os.path.join(db_dir, f'{name}_confirmed_{block}')
    open(new_path, 'w').close()
    for path, _ in _confirmed_files(db_dir, name):
        if path != new_path:
            try:
                os.remove(path)
            except OSError:
                pass
    print(f"[confirmed] {name}: advanced to {block}")
    return block


def rollback_watermark(db_dir, name, block):
    """把水位线回退到 block (只后退不前进)。用于 wrong_block 删块后。"""
    current = read_watermark(db_dir, name)
    if current is None or block >= current:
        return
    new_path = os.path.join(db_dir, f'{name}_good_{block}')
    open(new_path, 'w').close()
    for path, old_block in _files(db_dir, name):
        if path != new_path:
            try:
                os.remove(path)
            except OSError:
                pass
    print(f"[watermark] {name}: rolled back {current} -> {block}")
