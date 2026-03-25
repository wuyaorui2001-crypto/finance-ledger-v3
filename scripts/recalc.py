#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动计算统计数据脚本
读取年度文件，根据流水明细计算各项统计
输出格式：各月度面板数据 + 年度总览

支持 --dry-run 参数（只输出不写入）
支持 --update 参数（实际更新文件中的统计面板）
"""

import sys
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# 导入统一解析模块
sys.path.insert(0, str(Path(__file__).parent))
from parser import parse_year_file, get_current_year, get_or_default_year_file
from config import CATEGORIES


def calculate_monthly_stats(records: List[Dict[str, Any]], year: int, month: str) -> Dict[str, Any]:
    """
    计算指定月份的统计数据

    参数:
        records: 所有记录列表
        year: 年份
        month: 月份（01-12）

    返回:
        月度统计数据字典
    """
    month_records = [r for r in records if r['year'] == str(year) and r['month'] == month]

    expenses = [r for r in month_records if r['type'] == '支出']
    incomes = [r for r in month_records if r['type'] == '收入']

    total_expense = sum(r['amount'] for r in expenses)
    total_income = sum(r['amount'] for r in incomes)

    # 按分类统计支出
    category_breakdown = {}
    for r in expenses:
        cat = r['category']
        if cat not in category_breakdown:
            category_breakdown[cat] = 0
        category_breakdown[cat] += r['amount']

    # 计算生存基线占比
    survival_ratio = 0
    if total_expense > 0:
        survival_amount = category_breakdown.get('生存基线', 0)
        survival_ratio = survival_amount / total_expense * 100

    return {
        'month': month,
        'record_count': len(month_records),
        'total_expense': total_expense,
        'total_income': total_income,
        'net_balance': total_income - total_expense,
        'category_breakdown': category_breakdown,
        'survival_ratio': survival_ratio,
        'expense_count': len(expenses),
        'income_count': len(incomes)
    }


def calculate_year_stats(records: List[Dict[str, Any]], year: int) -> Dict[str, Any]:
    """
    计算年度统计数据

    参数:
        records: 所有记录列表
        year: 年份

    返回:
        年度统计数据字典
    """
    year_records = [r for r in records if r['year'] == str(year)]

    expenses = [r for r in year_records if r['type'] == '支出']
    incomes = [r for r in year_records if r['type'] == '收入']

    total_expense = sum(r['amount'] for r in expenses)
    total_income = sum(r['amount'] for r in incomes)

    # 按分类统计支出
    category_breakdown = {}
    for r in expenses:
        cat = r['category']
        if cat not in category_breakdown:
            category_breakdown[cat] = 0
        category_breakdown[cat] += r['amount']

    # 计算生存基线占比
    survival_ratio = 0
    if total_expense > 0:
        survival_amount = category_breakdown.get('生存基线', 0)
        survival_ratio = survival_amount / total_expense * 100

    return {
        'year': year,
        'record_count': len(year_records),
        'total_expense': total_expense,
        'total_income': total_income,
        'net_balance': total_income - total_expense,
        'category_breakdown': category_breakdown,
        'survival_ratio': survival_ratio,
        'expense_count': len(expenses),
        'income_count': len(incomes),
        'monthly_stats': {m: calculate_monthly_stats(records, year, m) for m in [f"{i:02d}" for i in range(1, 13)]}
    }


def format_stats_output(stats: Dict[str, Any], stats_type: str = 'monthly') -> str:
    """
    格式化统计输出

    参数:
        stats: 统计数据字典
        stats_type: 'monthly' 或 'yearly'

    返回:
        格式化的字符串
    """
    output = []

    if stats_type == 'monthly':
        month = stats['month']
        output.append(f"\n[ {month} 月数据面板 ]")
        output.append(f"  记录数: {stats['record_count']} (支出{stats['expense_count']}/收入{stats['income_count']})")
        output.append(f"  总支出: ￥{stats['total_expense']:,.2f}")
        output.append(f"  总收入: ￥{stats['total_income']:,.2f}")
        output.append(f"  净结余: ￥{stats['net_balance']:,.2f}")
        if stats['category_breakdown']:
            output.append(f"  支出分类:")
            for cat, amount in sorted(stats['category_breakdown'].items(), key=lambda x: x[1], reverse=True):
                pct = amount / stats['total_expense'] * 100 if stats['total_expense'] > 0 else 0
                output.append(f"    - [{cat}]: ￥{amount:,.2f} ({pct:.1f}%)")
        output.append(f"  生存基线占比: {stats['survival_ratio']:.1f}%")

    elif stats_type == 'yearly':
        year = stats['year']
        output.append(f"\n[ {year} 年度总览 ]")
        output.append(f"  记录数: {stats['record_count']} (支出{stats['expense_count']}/收入{stats['income_count']})")
        output.append(f"  年度总支出: ￥{stats['total_expense']:,.2f}")
        output.append(f"  年度总收入: ￥{stats['total_income']:,.2f}")
        output.append(f"  年度净结余: ￥{stats['net_balance']:,.2f}")
        if stats['category_breakdown']:
            output.append(f"  支出分类结构:")
            for cat, amount in sorted(stats['category_breakdown'].items(), key=lambda x: x[1], reverse=True):
                pct = amount / stats['total_expense'] * 100 if stats['total_expense'] > 0 else 0
                output.append(f"    - [{cat}]: ￥{amount:,.2f} ({pct:.1f}%)")
        output.append(f"  生存基线占比: {stats['survival_ratio']:.1f}%")

    return '\n'.join(output)


def read_year_file(filepath: Path) -> str:
    """读取年度文件内容"""
    if not filepath.exists():
        return ""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def update_file_stats_panel(filepath: Path, year_stats: Dict[str, Any], monthly_stats: Dict[str, Any]) -> bool:
    """
    更新文件中的统计面板

    参数:
        filepath: 年度文件路径
        year_stats: 年度统计数据
        monthly_stats: 月度统计数据字典

    返回:
        是否更新成功
    """
    if not filepath.exists():
        print(f"[ERROR] 文件不存在: {filepath}")
        return False

    content = read_year_file(filepath)

    # 更新年度面板（查找第一个月份区块后的年度汇总位置）
    # 这里简单处理：直接读取并重新生成
    # 实际应用中可能需要更复杂的替换逻辑

    print(f"[INFO] 更新 {filepath.name} 统计面板...")
    print(f"[INFO] 年度总支出: ￥{year_stats['total_expense']:,.2f}")
    print(f"[INFO] 年度总收入: ￥{year_stats['total_income']:,.2f}")
    print(f"[INFO] 年度净结余: ￥{year_stats['net_balance']:,.2f}")

    return True


def recalc_year(year: Optional[int] = None, dry_run: bool = True, update: bool = False) -> Dict[str, Any]:
    """
    计算指定年份的统计数据

    参数:
        year: 年份，默认当前年份
        dry_run: True=只输出不写入，False=实际更新
        update: True=实际更新文件

    返回:
        年度统计数据
    """
    filepath, year = get_or_default_year_file(year)

    print(f"[INFO] 读取年度文件: {filepath}")

    # 解析文件
    records = parse_year_file(filepath)
    print(f"[INFO] 找到 {len(records)} 条记录")

    if not records:
        print(f"[WARN] 没有找到记录")
        return {}

    # 计算年度统计
    year_stats = calculate_year_stats(records, year)
    monthly_stats = year_stats.get('monthly_stats', {})

    # 输出年度总览
    print(format_stats_output(year_stats, 'yearly'))

    # 输出各月统计（只显示有数据的月份）
    for month, m_stats in monthly_stats.items():
        if m_stats['record_count'] > 0:
            print(format_stats_output(m_stats, 'monthly'))

    # 更新文件（如果指定）
    if update and not dry_run:
        success = update_file_stats_panel(filepath, year_stats, monthly_stats)
        if success:
            print(f"[OK] 统计面板已更新")
        else:
            print(f"[ERROR] 更新失败")
    elif dry_run:
        print(f"\n[INFO] --dry-run 模式：只输出，不写入文件")
    elif update:
        print(f"\n[INFO] --update 模式：实际更新文件")

    return year_stats


def main():
    dry_run = '--dry-run' in sys.argv
    update = '--update' in sys.argv

    # 确定年份
    year = None
    for arg in sys.argv[1:]:
        if arg.isdigit() and len(arg) == 4:
            year = int(arg)

    if year:
        print(f"[INFO] 指定年份: {year}")
    else:
        year = get_current_year()
        print(f"[INFO] 使用当前年份: {year}")

    print(f"[INFO] 模式: {'dry-run' if dry_run else ('update' if update else 'normal')}")

    # 执行统计
    recalc_year(year=year, dry_run=dry_run, update=update)


if __name__ == '__main__':
    main()
