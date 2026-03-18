#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务账本可视化脚本
生成交互式HTML报表
"""

import re
import json
from datetime import datetime
from pathlib import Path
import sys

# 配置
PROJECT_DIR = Path(__file__).parent.parent
DATA_FILE = PROJECT_DIR / "2026.md"
OUTPUT_FILE = PROJECT_DIR / "reports" / "index.html"  # GitHub Pages 需要 index.html

def parse_ledger(filepath):
    """解析账本文件"""
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 匹配记录格式: - 2026-03-18 | 支出 | [分类] | #标签 | ￥金额 | 描述
    pattern = r'- (\d{4}-\d{2}-\d{2}) \| (\w+) \| \[(.+?)\] \| #(.+?) \| ￥([\d,\.]+) \| (.+)'
    
    for match in re.finditer(pattern, content):
        date_str, type_, category, tag, amount_str, desc = match.groups()
        amount = float(amount_str.replace(',', ''))
        records.append({
            'date': date_str,
            'type': type_,
            'category': category,
            'tag': tag,
            'amount': amount,
            'desc': desc.strip()
        })
    
    return records

def generate_dashboard(records):
    """生成HTML报表"""
    
    # 统计数据
    expenses = [r for r in records if r['type'] == '支出']
    incomes = [r for r in records if r['type'] == '收入']
    
    total_expense = sum(r['amount'] for r in expenses)
    total_income = sum(r['amount'] for r in incomes)
    
    # 按分类统计
    category_stats = {}
    for r in expenses:
        cat = r['category']
        category_stats[cat] = category_stats.get(cat, 0) + r['amount']
    
    # 按月份统计
    monthly_stats = {}
    for r in records:
        month = r['date'][:7]  # YYYY-MM
        if month not in monthly_stats:
            monthly_stats[month] = {'expense': 0, 'income': 0}
        if r['type'] == '支出':
            monthly_stats[month]['expense'] += r['amount']
        else:
            monthly_stats[month]['income'] += r['amount']
    
    # 生成HTML
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>财务账本可视化 - 2026</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; font-size: 28px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .stat-card h3 {{ margin: 0 0 10px 0; color: #666; font-size: 14px; }}
        .stat-card .value {{ font-size: 32px; font-weight: bold; color: #333; }}
        .stat-card .expense {{ color: #e74c3c; }}
        .stat-card .income {{ color: #27ae60; }}
        .stat-card .balance {{ color: {'#27ae60' if total_income >= total_expense else '#e74c3c'}; }}
        .chart-container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .chart-title {{ margin: 0 0 20px 0; font-size: 18px; color: #333; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 财务账本可视化报表</h1>
            <p>2026年度 | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>年度总支出</h3>
                <div class="value expense">￥{total_expense:,.2f}</div>
            </div>
            <div class="stat-card">
                <h3>年度总收入</h3>
                <div class="value income">￥{total_income:,.2f}</div>
            </div>
            <div class="stat-card">
                <h3>净结余</h3>
                <div class="value balance">￥{total_income - total_expense:,.2f}</div>
            </div>
            <div class="stat-card">
                <h3>记录总数</h3>
                <div class="value">{len(records)}</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2 class="chart-title">📈 月度收支趋势</h2>
            <div id="monthly-chart"></div>
        </div>
        
        <div class="chart-container">
            <h2 class="chart-title">🥧 支出分类占比</h2>
            <div id="category-chart"></div>
        </div>
    </div>
    
    <script>
        // 月度趋势图
        const monthlyData = {json.dumps(monthly_stats, ensure_ascii=False)};
        const months = Object.keys(monthlyData).sort();
        
        Plotly.newPlot('monthly-chart', [
            {{
                x: months,
                y: months.map(m => monthlyData[m].expense),
                type: 'bar',
                name: '支出',
                marker: {{ color: '#e74c3c' }}
            }},
            {{
                x: months,
                y: months.map(m => monthlyData[m].income),
                type: 'bar',
                name: '收入',
                marker: {{ color: '#27ae60' }}
            }}
        ], {{
            barmode: 'group',
            xaxis: {{ title: '月份' }},
            yaxis: {{ title: '金额 (￥)' }},
            hovermode: 'x unified'
        }});
        
        // 分类饼图
        const categoryData = {json.dumps(category_stats, ensure_ascii=False)};
        
        Plotly.newPlot('category-chart', [{{
            values: Object.values(categoryData),
            labels: Object.keys(categoryData),
            type: 'pie',
            hole: 0.4,
            textinfo: 'label+percent',
            textposition: 'outside'
        }}], {{
            showlegend: true,
            legend: {{ orientation: 'h', y: -0.1 }}
        }});
    </script>
</body>
</html>'''
    
    return html

def main():
    print("[INFO] 开始生成可视化报表...")
    
    # 检查数据文件
    if not DATA_FILE.exists():
        print(f"[ERROR] 数据文件不存在: {DATA_FILE}")
        sys.exit(1)
    
    # 创建输出目录
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    
    # 解析数据
    print(f"[INFO] 解析数据文件: {DATA_FILE}")
    records = parse_ledger(DATA_FILE)
    print(f"[INFO] 找到 {len(records)} 条记录")
    
    # 生成报表
    print("[INFO] 生成HTML报表...")
    html = generate_dashboard(records)
    
    # 保存文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"[OK] 报表已保存: {OUTPUT_FILE}")
    print(f"[INFO] 请在浏览器中打开查看")

if __name__ == '__main__':
    main()
