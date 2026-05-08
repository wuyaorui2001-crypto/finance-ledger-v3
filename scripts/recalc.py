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
    """
    if not filepath.exists():
        print(f"[ERROR] 文件不存在: {filepath}")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read()

    year = year_stats['year']
    te = year_stats['total_expense']
    ti = year_stats['total_income']
    nb = year_stats['net_balance']
    cat_break = year_stats['category_breakdown']

    # 用锚点分段处理：找到每个章节的起止位置
    # 章节顺序：年度总览 → 分类结构 → 01月 → 02月 → ... → 12月
    # 每个章节：[标题行, ---分隔行, 内容]

    annual_start = raw.find(f"## 📊 {year}年度总览")
    if annual_start == -1:
        print("[ERROR] 未找到年度总览章节")
        return False

    # 年度总览表格替换（只替换4行数据，保留表头+分隔符+末尾空行）
    sep_line_pos = raw.find("|------|------|", annual_start)
    if sep_line_pos == -1:
        print("[ERROR] 未找到年度表格分隔符")
        return False

    # 分隔符行之后是数据行，找到数据行开始
    data_start = raw.find("\n", sep_line_pos) + 1
    # 跳过4行数据：年度总支出/总收入/净结余/月均支出
    data_end = data_start
    for _ in range(4):
        nl = raw.find("\n", data_end)
        if nl == -1:
            break
        data_end = nl + 1

    # 计算有支出的月份数，用于月均
    months_with_data = sum(1 for m in monthly_stats.values() if m.get('record_count', 0) > 0) or 1
    monthly_avg = te / months_with_data

    new_data = (
        f"| 年度总支出 | ￥{te:,.2f} |\n"
        f"| 年度总收入 | ￥{ti:,.2f} |\n"
        f"| 年度净结余 | ￥{nb:,.2f} |\n"
        f"| 月均支出 | ￥{monthly_avg:,.2f} |\n"
    )
    raw = raw[:data_start] + new_data + raw[data_end:]

    # 重新计算分类结构位置（因为上面替换可能改变了偏移量）
    annual_start_new = raw.find(f"## 📊 {year}年度总览")
    cat_start = raw.find("### 分类支出结构", annual_start_new)
    if cat_start != -1:
        # 找到所有分类行到下一个空行或非分类行
        line_pos = cat_start
        while line_pos < len(raw) and raw[line_pos] != '\n':
            line_pos += 1
        line_pos += 1  # past \n

        # 收集分类行
        cat_lines_end = line_pos
        while True:
            if raw[cat_lines_end:].startswith("- ["):
                end = raw.find("\n", cat_lines_end)
                cat_lines_end = end + 1
            else:
                break

        cat_lines_new = []
        for cat, amount in sorted(cat_break.items(), key=lambda x: x[1], reverse=True):
            pct = amount / te * 100 if te > 0 else 0
            cat_lines_new.append(f"- [{cat}]：￥{amount:,.2f}（{pct:.1f}%）")
        cat_block_new = "\n".join(cat_lines_new) + "\n\n"

        raw = raw[:line_pos] + cat_block_new + raw[cat_lines_end:]

    # 月度面板替换
    month_pattern = re.compile(r"^### (\d{2})月\s*$", re.MULTILINE)
    for m_match in month_pattern.finditer(raw):
        m = m_match.group(1)
        m_stats = monthly_stats.get(m, {})
        if m_stats.get('record_count', 0) == 0:
            continue

        section_start = m_match.start()
        # 找"#### 当月数据面板"
        panel_header_pos = raw.find("#### 当月数据面板", section_start)
        if panel_header_pos == -1:
            continue

        # 找到面板表格（从分隔符开始）
        sep_pos = raw.find("\n", panel_header_pos)
        if sep_pos == -1:
            continue
        sep_pos += 1  # past newline

        # 收集6行面板（| 指标 | 数值 | + |------|------| + 4个数据行）
        pos = sep_pos
        rows_collected = 0
        table_end = sep_pos
        while rows_collected < 6 and pos < len(raw):
            next_nl = raw.find("\n", pos)
            if next_nl == -1:
                break
            table_end = next_nl + 1
            rows_collected += 1
            pos = next_nl + 1

        m_te = m_stats['total_expense']
        m_ti = m_stats['total_income']
        m_nb = m_stats['net_balance']
        m_sr = m_stats['survival_ratio']
        new_panel = (
            "| 指标 | 数值 |\n"
            "|------|------|\n"
            f"| 总支出 | ￥{m_te:,.2f} |\n"
            f"| 总收入 | ￥{m_ti:,.2f} |\n"
            f"| 净结余 | ￥{m_nb:,.2f} |\n"
            f"| 生存基线占比 | {m_sr:.1f}% |\n"
        )
        raw = raw[:sep_pos] + new_panel + raw[table_end:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(raw)

    print(f"[INFO] 更新 {filepath.name} 统计面板...")
    print(f"[INFO] 年度总支出: ￥{te:,.2f}")
    print(f"[INFO] 年度总收入: ￥{ti:,.2f}")
    print(f"[INFO] 年度净结余: ￥{nb:,.2f}")
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
