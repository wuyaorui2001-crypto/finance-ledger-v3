#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务账本分析脚本 - 支持多年数据汇总
用于生成跨年度统计和趋势分析
"""

import re
import json
from pathlib import Path
from collections import defaultdict
import sys

PROJECT_DIR = Path(__file__).parent.parent

def parse_year_file(filepath):
    """解析年度账本文件"""
    if not filepath.exists():
        return []
    
    records = []
    content = filepath.read_text(encoding='utf-8')
    
    # 匹配记录
    pattern = r'- (\d{4}-\d{2}-\d{2}) \| (\w+) \| \[(.+?)\] \| #(.+?) \| ￥([\d,\.]+) \| (.+)'
    
    for match in re.finditer(pattern, content):
        date_str, type_, category, tag, amount_str, desc = match.groups()
        records.append({
            'date': date_str,
            'year': date_str[:4],
            'month': date_str[5:7],
            'type': type_,
            'category': category,
            'tag': tag,
            'amount': float(amount_str.replace(',', '')),
            'desc': desc.strip()
        })
    
    return records

def analyze_all_years():
    """分析所有年度数据"""
    # 查找所有年度文件
    year_files = sorted(PROJECT_DIR.glob('2*.md'))
    
    all_records = []
    year_stats = {}
    
    for year_file in year_files:
        year = year_file.stem
        records = parse_year_file(year_file)
        all_records.extend(records)
        
        # 年度统计
        expenses = [r for r in records if r['type'] == '支出']
        incomes = [r for r in records if r['type'] == '收入']
        
        year_stats[year] = {
            'total_expense': sum(r['amount'] for r in expenses),
            'total_income': sum(r['amount'] for r in incomes),
            'record_count': len(records)
        }
    
    return all_records, year_stats

def generate_multi_year_report():
    """生成多年度分析报告"""
    records, year_stats = analyze_all_years()
    
    if not records:
        print("[ERROR] 没有找到记录")
        return
    
    # 总体统计
    all_expenses = [r for r in records if r['type'] == '支出']
    all_incomes = [r for r in records if r['type'] == '收入']
    
    total_expense = sum(r['amount'] for r in all_expenses)
    total_income = sum(r['amount'] for r in all_incomes)
    
    # 按分类统计（全部年份）
    category_stats = defaultdict(float)
    for r in all_expenses:
        category_stats[r['category']] += r['amount']
    
    # 按年月统计
    monthly_trend = defaultdict(lambda: {'expense': 0, 'income': 0})
    for r in records:
        ym = r['date'][:7]
        if r['type'] == '支出':
            monthly_trend[ym]['expense'] += r['amount']
        else:
            monthly_trend[ym]['income'] += r['amount']
    
    # 生成报告
    report = f"""# 📊 多年度财务分析报告

> 生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}
> 数据范围: {min(r['year'] for r in records)} - {max(r['year'] for r in records)}

---

## 总体概览

| 指标 | 数值 |
|------|------|
| 统计年份 | {len(year_stats)} 年 |
| 总记录数 | {len(records)} 条 |
| 总支出 | ￥{total_expense:,.2f} |
| 总收入 | ￥{total_income:,.2f} |
| 净结余 | ￥{total_income - total_expense:,.2f} |
| 年均支出 | ￥{total_expense / len(year_stats):,.2f} |

---

## 年度对比

| 年份 | 支出 | 收入 | 结余 | 记录数 |
|------|------|------|------|--------|
"""
    
    for year in sorted(year_stats.keys()):
        stats = year_stats[year]
        balance = stats['total_income'] - stats['total_expense']
        report += f"| {year} | ￥{stats['total_expense']:,.2f} | ￥{stats['total_income']:,.2f} | ￥{balance:,.2f} | {stats['record_count']} |\n"
    
    report += """
---

## 分类支出结构（全部年份）

| 分类 | 金额 | 占比 |
|------|------|------|
"""
    
    for cat, amount in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
        pct = amount / total_expense * 100 if total_expense > 0 else 0
        report += f"| [{cat}] | ￥{amount:,.2f} | {pct:.1f}% |\n"
    
    report += """
---

## 使用说明

本报告由 `scripts/analyze.py` 自动生成，汇总所有年度数据。

**更新方法**:
```bash
python scripts/analyze.py
```

**数据文件**: 每个年度的数据存储在 `2XXX.md` 文件中

---

*账本系统 v3.1 | 支持10年+长期记账*
"""
    
    # 保存报告
    output_file = PROJECT_DIR / 'INDEX.md'
    output_file.write_text(report, encoding='utf-8')
    
    print(f"[OK] 分析报告已生成: {output_file}")
    print(f"[INFO] 统计年份: {len(year_stats)} 年")
    print(f"[INFO] 总记录数: {len(records)} 条")

if __name__ == '__main__':
    generate_multi_year_report()
