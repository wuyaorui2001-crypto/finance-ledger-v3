#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一解析模块
提供标准接口解析账本记录

接口说明:
- parse_record(line): 解析单条记账记录
- parse_year_file(filepath): 解析年度文件，返回所有记录列表
- get_current_year(): 获取当前应记账的年份（基于实际日期）
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from config import LEDGER_CATEGORIES, YEAR_FILES_PATH


# 记账记录正则（与 validate.py 保持一致）
RECORD_PATTERN = re.compile(
    r'^- (\d{4}-\d{2}-\d{2})\s+'
    r'\|\s*(收入|支出)\s*\|\s*'
    r'\[([^\]]+)\]\s*\|\s*'
    r'(#[^\s|]+)\s*\|\s*'
    r'[￥¥]([\d,]+\.?\d*)\s*\|\s*'
    r'(.+)$'
)


def parse_record(line: str) -> Optional[Dict[str, Any]]:
    """
    解析单条记账记录

    参数:
        line: 账本行，如 "- 2026-03-18 | 支出 | [生存基线] | #午饭 | ￥25.00 | 午饭25"

    返回:
        解析成功返回字典，包含字段: date, type, category, tag, amount, desc
        解析失败返回 None
    """
    line = line.strip()
    if not line.startswith('- 20'):
        return None

    match = RECORD_PATTERN.match(line)
    if not match:
        return None

    date_str, record_type, category, tag, amount_str, desc = match.groups()

    return {
        'date': date_str,
        'type': record_type,
        'category': category,
        'tag': tag,
        'amount': float(amount_str.replace(',', '')),
        'desc': desc.strip(),
        'year': date_str[:4],
        'month': date_str[5:7]
    }


def parse_year_file(filepath: Path) -> List[Dict[str, Any]]:
    """
    解析年度文件，返回所有记录列表

    参数:
        filepath: 年度文件路径，如 Path("2026.md")

    返回:
        记录字典列表，每条记录包含: date, type, category, tag, amount, desc, year, month
    """
    records = []

    if not filepath.exists():
        return records

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            record = parse_record(line)
            if record:
                records.append(record)

    return records


def get_current_year() -> int:
    """
    获取当前应记账的年份（基于实际日期）

    基于系统当前日期判断，不是基于文件存在性。
    遵循 PATTERN-006 元数据标记必须交叉验证原则。

    返回:
        当前年份整数，如 2026
    """
    return datetime.now().year


def get_active_year_file() -> Path:
    """
    获取当前应记录的年度文件路径

    返回:
        Path: 当前年度文件路径
    """
    current_year = get_current_year()
    return YEAR_FILES_PATH / f"{current_year}.md"


def get_tag_category(tag: str) -> str:
    """
    根据子标签获取主分类

    参数:
        tag: 子标签，如 "#午饭"

    返回:
        主分类名称，如果未找到返回 None
    """
    # 移除 # 前缀
    tag_name = tag.lstrip('#')
    return LEDGER_CATEGORIES.get(tag_name)


def get_or_default_year_file(year: Optional[int] = None) -> tuple[Path, int]:
    """
    获取指定年份的文件路径，不存在则返回当前年份

    参数:
        year: 年份整数，如 2026。None 则使用当前年份。

    返回:
        tuple[Path, int]: (文件路径, 实际年份)
    """
    if year is None:
        year = get_current_year()
    return YEAR_FILES_PATH / f"{year}.md", year
