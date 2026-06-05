#!/usr/bin/env python3
"""One-off migration: income/expense sections + June chapter for 2026.md"""
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).parent))
from parser import parse_year_file

PROJECT = Path(__file__).parent.parent
FILE = PROJECT / "2026.md"

INCOME_TEMPLATE = {
    "01": "- 2026-01-01 | 收入 | [资金流入] | #工资 | ￥3,100.00 | 1月工资",
    "02": "- 2026-02-01 | 收入 | [资金流入] | #工资 | ￥3,100.00 | 2月工资",
    "03": "- 2026-03-01 | 收入 | [资金流入] | #工资 | ￥3,100.00 | 3月工资",
    "04": "- 2026-04-01 | 收入 | [资金流入] | #工资 | ￥3,100.00 | 4月工资",
    "05": "- 2026-05-01 | 收入 | [资金流入] | #工资 | ￥3,100.00 | 5月工资",
    "06": "- 2026-06-01 | 收入 | [资金流入] | #工资 | ￥3,100.00 | 6月工资",
}


def record_to_line(r: dict) -> str:
    amt = f"￥{r['amount']:,.2f}"
    return f"- {r['date']} | {r['type']} | [{r['category']}] | {r['tag']} | {amt} | {r['desc']}"


def main():
    raw = FILE.read_text(encoding="utf-8")
    eof = raw.find("--- EOF ---")
    if eof == -1:
        raise SystemExit("EOF marker missing")

    prefix = raw[:eof]
    records = parse_year_file(FILE)
    expenses_by_month: dict[str, list] = {}
    for r in records:
        if r["type"] != "支出":
            continue
        m = r["month"]
        expenses_by_month.setdefault(m, []).append(r)

    # find first month section
    first_month = prefix.find("### 01月")
    if first_month == -1:
        raise SystemExit("### 01月 not found")
    head = prefix[:first_month]

    parts = [head.rstrip(), ""]
    for mm in ["01", "02", "03", "04", "05", "06"]:
        exp = expenses_by_month.get(mm, [])
        if not exp and mm not in INCOME_TEMPLATE:
            continue
        parts.append(f"### {mm}月")
        parts.append("")
        parts.append("#### 当月数据面板")
        parts.append("| 指标 | 数值 |")
        parts.append("|------|------|")
        parts.append("| 总支出 | ￥0.00 |")
        parts.append("| 总收入 | ￥0.00 |")
        parts.append("| 净结余 | ￥0.00 |")
        parts.append("| 支出占收入 | 0% |")
        parts.append("| 生存基线占比 | 0% |")
        parts.append("")
        parts.append("#### 当月收入")
        if mm in INCOME_TEMPLATE:
            parts.append(INCOME_TEMPLATE[mm])
        parts.append("")
        parts.append("#### 当月支出明细")
        for r in sorted(exp, key=lambda x: x["date"]):
            parts.append(record_to_line(r))
        parts.append("")

    parts.append("--- EOF ---")
    parts.append("")
    FILE.write_text("\n".join(parts), encoding="utf-8")
    print(f"[OK] migrated {FILE.name}: {len(records)} records, months 01-06")


if __name__ == "__main__":
    main()
