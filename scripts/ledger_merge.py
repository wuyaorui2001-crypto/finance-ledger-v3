#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
年度账本三方合并：以流水行为单位，把本地新增/删除的记录叠加到远程版本上。

面板数字不参与合并，合并后由 recalc.py 重算。
"""

import re
from collections import Counter

RECORD_RE = re.compile(r'^- (\d{4}-(\d{2})-\d{2})\s*\|\s*(收入|支出)\s*\|')
AMOUNT_RE = re.compile(r'[￥¥]([\d,]+\.?\d*)')
TAG_RE = re.compile(r'\]\s*\|\s*(#[^\s|]+)')
EOF_MARK = '--- EOF ---'
INCOME_HEADER = '#### 当月收入'
EXPENSE_HEADERS = ('#### 当月支出明细', '#### 当月流水明细')


def record_counter(text):
    if not text:
        return Counter()
    return Counter(
        line.rstrip() for line in text.splitlines() if RECORD_RE.match(line.rstrip())
    )


def month_skeleton(mm):
    return [
        f'### {mm}月',
        '',
        '#### 当月数据面板',
        '| 指标 | 数值 |',
        '|------|------|',
        '| 总支出 | ￥0.00 |',
        '| 总收入 | ￥0.00 |',
        '| 净结余 | ￥0.00 |',
        '| 支出占收入 | 0% |',
        '| 生存基线占比 | 0% |',
        '',
        INCOME_HEADER,
        '',
        '> 暂无收入记录',
        '',
        EXPENSE_HEADERS[0],
        '',
        '> 暂无支出记录',
        '',
    ]


def _month_of_heading(line):
    m = re.match(r'^### (\d{2})月\s*$', line)
    return m.group(1) if m else None


def _find_month(lines, mm):
    for i, line in enumerate(lines):
        if _month_of_heading(line) == mm:
            return i
    return None


def _ensure_month(lines, mm):
    idx = _find_month(lines, mm)
    if idx is not None:
        return idx
    insert_at = None
    for i, line in enumerate(lines):
        other = _month_of_heading(line)
        if other and other > mm:
            insert_at = i
            break
        if line.strip() == EOF_MARK:
            insert_at = i
            break
    if insert_at is None:
        insert_at = len(lines)
    lines[insert_at:insert_at] = month_skeleton(mm)
    return insert_at


def _block_end(lines, start):
    for i in range(start + 1, len(lines)):
        if lines[i].startswith('### ') or lines[i].strip() == EOF_MARK:
            return i
    return len(lines)


def _insert_record(lines, record):
    m = RECORD_RE.match(record)
    date, mm, kind = m.group(1), m.group(2), m.group(3)
    month_start = _ensure_month(lines, mm)
    month_end = _block_end(lines, month_start)
    headers = (INCOME_HEADER,) if kind == '收入' else EXPENSE_HEADERS

    header_idx = None
    for i in range(month_start, month_end):
        if lines[i].rstrip() in headers:
            header_idx = i
            break
    if header_idx is None:
        header_idx = month_end
        lines[header_idx:header_idx] = ['', headers[0], '']
        month_end += 3

    section_end = month_end
    for i in range(header_idx + 1, month_end):
        if lines[i].startswith('#### '):
            section_end = i
            break

    placeholder = None
    last_before = None
    first_record = None
    for i in range(header_idx + 1, section_end):
        line = lines[i].rstrip()
        if line.startswith('> 暂无'):
            placeholder = i
        rm = RECORD_RE.match(line)
        if rm:
            if first_record is None:
                first_record = i
            if rm.group(1) <= date:
                last_before = i

    if placeholder is not None and first_record is None:
        lines[placeholder] = record
    elif last_before is not None:
        lines.insert(last_before + 1, record)
    elif first_record is not None:
        lines.insert(first_record, record)
    else:
        lines.insert(header_idx + 1, record)


def _remove_record(lines, record, count):
    for i in range(len(lines) - 1, -1, -1):
        if count <= 0:
            break
        if lines[i].rstrip() == record:
            del lines[i]
            count -= 1


def _record_key(line):
    """日期 + 子标签 + 金额，用于识别两端各记了一次的同一笔"""
    m = RECORD_RE.match(line)
    tag = TAG_RE.search(line)
    amount = AMOUNT_RE.search(line)
    if not m or not tag or not amount:
        return None
    return m.group(1), tag.group(1), f"{float(amount.group(1).replace(',', '')):.2f}"


def merge_year_text(base, ours, theirs, duplicates='keep'):
    """
    返回 (合并后文本, 本地新增条数, 本地删除条数, 疑似重复列表)。
    ours/theirs 为 None 表示该侧没有这个文件。

    疑似重复 = 本地新增的记录，与远程同期新增的记录日期、子标签、金额都相同。
    duplicates='keep' 两条都保留；'drop' 丢弃本地这条，以远程为准。
    疑似重复列表元素为 (本地记录, 远程记录)。
    """
    if theirs is None:
        return ours, 0, 0, []
    if ours is None:
        return theirs, 0, 0, []

    b, o, t = record_counter(base), record_counter(ours), record_counter(theirs)
    lines = theirs.splitlines()
    added = removed = 0

    for record in sorted(set(o) | set(b)):
        delta = o[record] - b[record]
        if delta < 0:
            _remove_record(lines, record, -delta)
            removed += -delta

    remote_added = Counter()
    remote_by_key = {}
    for record, n in t.items():
        key = _record_key(record)
        if key and n - b[record] > 0:
            remote_added[key] += n - b[record]
            remote_by_key.setdefault(key, record)

    suspects = []
    for record in sorted(o, key=lambda r: RECORD_RE.match(r).group(1)):
        delta = o[record] - b[record]
        key = _record_key(record)
        for _ in range(max(delta, 0)):
            if key and remote_added[key] > 0:
                remote_added[key] -= 1
                suspects.append((record, remote_by_key[key]))
                if duplicates == 'drop':
                    continue
            _insert_record(lines, record)
            added += 1

    merged = '\n'.join(lines)
    if theirs.endswith('\n'):
        merged += '\n'
    return merged, added, removed, suspects
