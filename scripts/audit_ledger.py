#!/usr/bin/env python3
"""Fine-grained finance ledger audit."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parser import parse_year_file
from recalc import calculate_monthly_stats, calculate_year_stats

PROJECT = Path(__file__).parent.parent
YEAR = 2026
FILE = PROJECT / f"{YEAR}.md"
DATA_JSON = PROJECT / "reports" / "data.json"


def parse_sections(content: str) -> dict:
    """Parse month sections and subsections."""
    months = {}
    current_month = None
    current_section = None
    for i, line in enumerate(content.splitlines(), 1):
        s = line.strip()
        m = re.match(r"^### (\d{2})月\s*$", s)
        if m:
            current_month = m.group(1)
            months[current_month] = {
                "header_line": i,
                "sections": set(),
                "income_lines": [],
                "expense_lines": [],
                "panel_rows": {},
            }
            current_section = None
            continue
        if current_month is None:
            continue
        if s == "#### 当月收入":
            current_section = "income"
            months[current_month]["sections"].add("income")
            continue
        if s in ("#### 当月支出明细", "#### 当月流水明细"):
            current_section = "expense"
            months[current_month]["sections"].add("expense")
            continue
        if s == "#### 当月数据面板":
            current_section = "panel"
            months[current_month]["sections"].add("panel")
            continue
        if s.startswith("- 20") and current_section == "income":
            months[current_month]["income_lines"].append((i, s))
        elif s.startswith("- 20") and current_section == "expense":
            months[current_month]["expense_lines"].append((i, s))
        elif current_section == "panel" and s.startswith("|") and not s.startswith("| ---"):
            parts = [p.strip() for p in s.strip("|").split("|")]
            if len(parts) == 2 and parts[0] != "指标" and not parts[0].startswith("-"):
                months[current_month]["panel_rows"][parts[0]] = parts[1]
    return months


def audit() -> dict:
    content = FILE.read_text(encoding="utf-8")
    records = parse_year_file(FILE)
    year_stats = calculate_year_stats(records, YEAR)
    sections = parse_sections(content)

    issues = {"errors": [], "warnings": [], "info": []}

    # EOF
    if "--- EOF ---" not in content:
        issues["errors"].append("缺少 --- EOF --- 标记")
    else:
        after = content.split("--- EOF ---", 1)[1].strip()
        if after:
            issues["errors"].append(f"EOF 之后有残留内容 ({len(after)} chars)")

    # Year overview vs computed
    ym = re.search(r"\| 年度总支出 \| ￥([\d,\.]+)", content)
    yi = re.search(r"\| 年度总收入 \| ￥([\d,\.]+)", content)
    yn = re.search(r"\| 年度净结余 \| ￥(-?[\d,\.]+)", content)
    yer = re.search(r"\| 支出占收入 \| ([\d\.]+)%", content)
    if ym and abs(float(ym.group(1).replace(",", "")) - year_stats["total_expense"]) > 0.01:
        issues["errors"].append(
            f"年度总览支出不一致: 面板 {ym.group(1)} vs 明细 {year_stats['total_expense']:.2f}"
        )
    if yi and abs(float(yi.group(1).replace(",", "")) - year_stats["total_income"]) > 0.01:
        issues["errors"].append(
            f"年度总览收入不一致: 面板 {yi.group(1)} vs 明细 {year_stats['total_income']:.2f}"
        )
    if yn and abs(float(yn.group(1).replace(",", "")) - year_stats["net_balance"]) > 0.01:
        issues["errors"].append(
            f"年度总览净结余不一致: 面板 {yn.group(1)} vs 明细 {year_stats['net_balance']:.2f}"
        )
    comp_er = year_stats.get("expense_ratio", 0)
    if yer and abs(float(yer.group(1)) - comp_er) > 0.15:
        issues["errors"].append(f"年度支出占收入不一致: 面板 {yer.group(1)}% vs 明细 {comp_er:.1f}%")

    # Income records audit
    incomes = [r for r in records if r["type"] == "收入"]
    expenses = [r for r in records if r["type"] == "支出"]
    issues["info"].append(f"总记录 {len(records)}: 支出 {len(expenses)} + 收入 {len(incomes)}")

    salary = [r for r in incomes if r["tag"] == "#工资"]
    for r in salary:
        if r["amount"] != 3100.0:
            issues["warnings"].append(f"{r['date']} 工资金额 {r['amount']} != 3100")
        if not r["date"].endswith("-01"):
            issues["warnings"].append(f"{r['date']} 工资日期不是每月1日")
        if r["category"] != "资金流入":
            issues["errors"].append(f"{r['date']} 工资主分类错误: {r['category']}")

    expected_salary_months = {"01", "02", "03", "04", "05", "06"}
    got_months = {r["month"] for r in salary}
    missing = expected_salary_months - got_months
    extra = got_months - expected_salary_months
    if missing:
        issues["errors"].append(f"缺少工资月份: {sorted(missing)}")
    if extra:
        issues["warnings"].append(f"额外工资月份: {sorted(extra)}")
    if len(salary) != 6:
        issues["warnings"].append(f"工资条数 {len(salary)}，期望 6")

    # Monthly structure + panel vs computed
    month_detail = []
    for mm in sorted(sections.keys()):
        sec = sections[mm]
        ms = calculate_monthly_stats(records, YEAR, mm)
        row = {
            "month": mm,
            "sections": sorted(sec["sections"]),
            "income_lines": len(sec["income_lines"]),
            "expense_lines": len(sec["expense_lines"]),
            "computed_expense": round(ms["total_expense"], 2),
            "computed_income": round(ms["total_income"], 2),
            "computed_ratio": round(ms.get("expense_ratio", 0), 1),
        }
        if "panel" not in sec["sections"]:
            issues["errors"].append(f"{mm}月 缺少 #### 当月数据面板")
        if "income" not in sec["sections"]:
            issues["warnings"].append(f"{mm}月 缺少 #### 当月收入 区块")
        if "expense" not in sec["sections"]:
            issues["warnings"].append(f"{mm}月 缺少 #### 当月支出明细 区块")
        if sec["sections"] and "expense" in sec["sections"] and sec["expense_lines"] == [] and ms["total_expense"] > 0:
            issues["errors"].append(f"{mm}月 有支出金额但支出明细区块无行")

        panel = sec["panel_rows"]
        for key, comp_key, fmt in [
            ("总支出", "computed_expense", "money"),
            ("总收入", "computed_income", "money"),
            ("支出占收入", "computed_ratio", "pct"),
        ]:
            if key not in panel:
                if ms["record_count"] > 0:
                    issues["warnings"].append(f"{mm}月 面板缺少行: {key}")
                continue
            val = panel[key]
            if fmt == "money":
                pv = float(val.replace("￥", "").replace(",", ""))
                cv = row[comp_key]
                if abs(pv - cv) > 0.01:
                    issues["errors"].append(f"{mm}月 面板{key} {pv} != 明细 {cv}")
            else:
                pv = float(val.replace("%", ""))
                if abs(pv - row[comp_key]) > 0.15:
                    issues["errors"].append(f"{mm}月 面板{key} {pv}% != 明细 {row[comp_key]}%")

        # income in wrong section (from file structure)
        for ln, _ in sec["expense_lines"]:
            pass  # already partitioned by parser walk
        month_detail.append(row)

    # Orphan records: income not in income section
    for mm, sec in sections.items():
        for ln, line in sec["expense_lines"]:
            if "| 收入 |" in line:
                issues["errors"].append(f"第{ln}行: 收入记录在支出明细区块")
        for ln, line in sec["income_lines"]:
            if "| 支出 |" in line:
                issues["errors"].append(f"第{ln}行: 支出记录在收入区块")

    # Duplicate exact lines
    from collections import Counter
    lines = [l.strip() for l in content.splitlines() if l.strip().startswith("- 20")]
    dups = [l for l, c in Counter(lines).items() if c > 1]
    for d in dups[:5]:
        issues["warnings"].append(f"完全重复行: {d[:60]}...")

    # Same day same tag multiple
    by_dt = defaultdict(list)
    for r in records:
        by_dt[(r["date"], r["tag"], r["type"])].append(r)
    multi = {k: v for k, v in by_dt.items() if len(v) > 1}
    for (d, t, tp), items in sorted(multi.items())[:10]:
        amts = "+".join(f"{x['amount']:g}" for x in items)
        issues["info"].append(f"同日同标签 {d} {tp} {t}: {len(items)}条 ({amts})")

    # data.json vs ledger
    if DATA_JSON.exists():
        dj = json.loads(DATA_JSON.read_text(encoding="utf-8"))
        y = dj.get("years", {}).get(str(YEAR), {})
        if y:
            checks = [
                ("total_expense", year_stats["total_expense"]),
                ("total_income", year_stats["total_income"]),
                ("net_balance", year_stats["net_balance"]),
                ("expense_ratio", year_stats.get("expense_ratio", 0)),
            ]
            for k, cv in checks:
                dv = y.get(k)
                if dv is not None and abs(float(dv) - float(cv)) > 0.02:
                    issues["errors"].append(f"data.json {k}={dv} != 账本 {cv:.2f}")
            for m in y.get("months", []):
                if not m.get("has_data"):
                    continue
                mm = m["month"]
                cms = calculate_monthly_stats(records, YEAR, mm)
                for k in ("income", "expense", "balance"):
                    if k in m and abs(m[k] - cms[{"income": "total_income", "expense": "total_expense", "balance": "net_balance"}[k]]) > 0.02:
                        issues["errors"].append(f"data.json {mm}月 {k}={m[k]} != 账本")
        else:
            issues["warnings"].append("data.json 无 2026 年数据")
    else:
        issues["warnings"].append("reports/data.json 不存在")

    # Trailing pipe on lines
    trail = sum(1 for l in lines if l.rstrip().endswith("|"))
    if trail:
        issues["info"].append(f"行尾多余 | 的记录: {trail} 条")

    # 日结补录 stats
    bulk = [r for r in expenses if r["tag"] == "#日结补录"]
    issues["info"].append(f"日结补录: {len(bulk)} 条, 合计 ￥{sum(r['amount'] for r in bulk):,.2f}")

    # Q2 no income in file beyond salary
    q2_other_income = [r for r in incomes if r["month"] in ("04", "05", "06") and r["tag"] != "#工资"]
    if q2_other_income:
        issues["info"].append(f"4-6月非工资收入: {len(q2_other_income)} 条")

    return {
        "year": YEAR,
        "year_computed": {
            "expense": round(year_stats["total_expense"], 2),
            "income": round(year_stats["total_income"], 2),
            "balance": round(year_stats["net_balance"], 2),
            "expense_ratio": round(year_stats.get("expense_ratio", 0), 1),
        },
        "month_detail": month_detail,
        "salary_records": [{"date": r["date"], "amount": r["amount"]} for r in sorted(salary, key=lambda x: x["date"])],
        **issues,
    }


if __name__ == "__main__":
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2))
