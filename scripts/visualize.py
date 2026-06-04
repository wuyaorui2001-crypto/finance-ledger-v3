#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务账本可视化脚本
生成 GitHub Pages 仪表盘（data.json + index.html）
"""

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))
from config import PROJECT_DIR
from parser import get_current_year, parse_year_file
from recalc import calculate_year_stats

REPORTS_DIR = PROJECT_DIR / "reports"
ASSETS_DIR = REPORTS_DIR / "assets"
DATA_FILE = REPORTS_DIR / "data.json"
INDEX_FILE = REPORTS_DIR / "index.html"

MONTH_LABELS = {
    "01": "1月", "02": "2月", "03": "3月", "04": "4月",
    "05": "5月", "06": "6月", "07": "7月", "08": "8月",
    "09": "9月", "10": "10月", "11": "11月", "12": "12月",
}


def discover_year_files() -> List[Path]:
    """扫描项目根目录下的年度账本文件"""
    files = []
    for filepath in sorted(PROJECT_DIR.glob("20*.md")):
        if re.match(r"^\d{4}\.md$", filepath.name):
            files.append(filepath)
    return files


def _days_in_period(year: int, last_record_date: Optional[str]) -> int:
    """统计周期自然日数：当年至 min(今天, 末条记录)；历史年至 12/31"""
    start = date(year, 1, 1)
    today = date.today()

    if year < today.year:
        end = date(year, 12, 31)
    elif year == today.year:
        if last_record_date:
            last = date.fromisoformat(last_record_date)
            end = min(today, last)
        else:
            end = today
    else:
        end = start

    return max((end - start).days + 1, 1)


def compute_year_dashboard_stats(records: List[Dict[str, Any]], year: int) -> Dict[str, Any]:
    """计算单年度仪表盘统计数据"""
    year_stats = calculate_year_stats(records, year)
    monthly_stats = year_stats["monthly_stats"]

    year_records = [r for r in records if r["year"] == str(year)]
    expense_dates = [r["date"] for r in year_records if r["type"] == "支出"]
    last_record_date = max(expense_dates) if expense_dates else None

    total_expense = year_stats["total_expense"]
    months_with_data = sum(
        1 for m in monthly_stats.values() if m.get("record_count", 0) > 0
    )
    monthly_avg = total_expense / (months_with_data or 1)

    days_in_period = _days_in_period(year, last_record_date)
    daily_avg = total_expense / days_in_period if total_expense > 0 else 0.0

    months = []
    for m in [f"{i:02d}" for i in range(1, 13)]:
        ms = monthly_stats[m]
        months.append({
            "month": m,
            "label": MONTH_LABELS[m],
            "expense": round(ms["total_expense"], 2),
            "has_data": ms["record_count"] > 0,
        })

    categories = []
    if total_expense > 0:
        for name, amount in sorted(
            year_stats["category_breakdown"].items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            if name == "资金流入":
                continue
            categories.append({
                "name": name,
                "amount": round(amount, 2),
                "percent": round(amount / total_expense * 100, 1),
            })

    return {
        "total_expense": round(total_expense, 2),
        "monthly_avg": round(monthly_avg, 2),
        "daily_avg": round(daily_avg, 2),
        "months": months,
        "categories": categories,
        "meta": {
            "months_with_data": months_with_data,
            "days_in_period": days_in_period,
            "last_record_date": last_record_date,
            "record_count": year_stats["record_count"],
        },
    }


def build_dashboard_data(all_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """聚合所有年度数据为 data.json 结构"""
    year_files = discover_year_files()
    years: Dict[str, Any] = {}

    for filepath in year_files:
        year = int(filepath.stem)
        records = parse_year_file(filepath)
        years[str(year)] = compute_year_dashboard_stats(records, year)

    default_year = get_current_year()
    if str(default_year) not in years and years:
        default_year = max(int(y) for y in years.keys())

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "default_year": default_year,
        "years": years,
    }


def generate_index_html() -> str:
    """生成静态 HTML 壳（样式与逻辑在 assets/）"""
    return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>冰美式财务账本</title>
    <link rel="stylesheet" href="./assets/dashboard.css">
</head>
<body>
    <div class="grain"></div>
    <div class="page">
        <header class="header">
            <div class="header-main">
                <p class="eyebrow">Personal Finance Ledger</p>
                <h1 class="title">冰美式财务账本</h1>
                <p class="updated" id="updated-at">加载中…</p>
            </div>
            <nav class="year-switcher" id="year-switcher" aria-label="切换年份"></nav>
        </header>

        <div class="empty-inline hidden" id="empty-inline">
            <p><strong id="empty-year-label">—</strong> 年度暂无记账数据</p>
        </div>

        <div id="page-data">
        <section class="kpi-section" aria-label="支出概览">
            <article class="kpi-card" style="--delay: 0">
                <span class="kpi-label">总支出</span>
                <span class="kpi-value" id="kpi-total">—</span>
            </article>
            <article class="kpi-card" style="--delay: 1">
                <span class="kpi-label">月均支出</span>
                <span class="kpi-value" id="kpi-monthly">—</span>
            </article>
            <article class="kpi-card" style="--delay: 2">
                <span class="kpi-label">日均支出</span>
                <span class="kpi-value" id="kpi-daily">—</span>
            </article>
        </section>

        <section class="panel" aria-label="每月支出">
            <div class="panel-head">
                <h2 class="panel-title">每月支出</h2>
                <p class="panel-sub" id="monthly-sub"></p>
            </div>
            <div class="monthly-chart" id="monthly-chart"></div>
            <table class="data-table" id="monthly-table">
                <thead>
                    <tr><th>月份</th><th>支出</th></tr>
                </thead>
                <tbody></tbody>
            </table>
        </section>

        <section class="panel" aria-label="类目结构">
            <div class="panel-head">
                <h2 class="panel-title">类目结构</h2>
                <p class="panel-sub">按支出金额排序</p>
            </div>
            <div class="category-bars" id="category-bars"></div>
            <table class="data-table" id="category-table">
                <thead>
                    <tr><th>类目</th><th>金额</th><th>占比</th></tr>
                </thead>
                <tbody></tbody>
            </table>
        </section>

        <footer class="footnote" id="footnote"></footer>
        </div>
    </div>

    <script src="./assets/dashboard.js"></script>
</body>
</html>'''


def main():
    print("[INFO] 开始生成可视化报表...")

    REPORTS_DIR.mkdir(exist_ok=True)
    ASSETS_DIR.mkdir(exist_ok=True)

    year_files = discover_year_files()
    print(f"[INFO] 发现 {len(year_files)} 个年度文件")

    all_records: List[Dict[str, Any]] = []
    for filepath in year_files:
        records = parse_year_file(filepath)
        all_records.extend(records)
        print(f"  - {filepath.name}: {len(records)} 条")

    dashboard_data = build_dashboard_data(all_records)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
    print(f"[OK] 数据已保存: {DATA_FILE}")

    html = generate_index_html()
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] 页面已保存: {INDEX_FILE}")

    default = dashboard_data["default_year"]
    if str(default) in dashboard_data["years"]:
        y = dashboard_data["years"][str(default)]
        print(f"[INFO] {default} 年: 总支出 ￥{y['total_expense']:,.2f}, "
              f"月均 ￥{y['monthly_avg']:,.2f}, 日均 ￥{y['daily_avg']:,.2f}")


if __name__ == "__main__":
    main()
