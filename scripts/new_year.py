#!/usr/bin/env python3
"""
创建新年度账本模板
每年1月1日运行：python scripts/new_year.py 2028
"""

import sys
from pathlib import Path
from datetime import datetime


def month_block(mm: str, hint: str = "本月暂无数据") -> str:
    return f"""### {mm}月

#### 当月数据面板
| 指标 | 数值 |
|------|------|
| 总支出 | ￥0.00 |
| 总收入 | ￥0.00 |
| 净结余 | ￥0.00 |
| 支出占收入 | 0% |
| 生存基线占比 | 0% |

**第一性原理诊断：**
- {hint}

#### 当月收入

> 暂无收入记录

#### 当月支出明细

> 暂无支出记录

"""


def create_year_template(year: int):
    """创建指定年份的账本模板"""
    base_dir = Path(__file__).parent.parent
    filepath = base_dir / f"{year}.md"

    if filepath.exists():
        print(f"⚠️ 文件已存在: {filepath}")
        return False

    template = f"""---
version: 3.2
currency: CNY
date_format: YYYY-MM-DD
data_structure: strict_modular_list
categories: [生存基线, 精力与健康维护, 杠杆与生产力, 资产与储备, 弹性消耗, 资金流入]
year: {year}
status: template
created_at: {datetime.now().strftime('%Y-%m-%d')}
---

> **[SYSTEM DIRECTIVE：记账规则]**
> 1. 支出追加到 `#### 当月支出明细`；收入追加到 `#### 当月收入`
> 2. 禁止自创主标签，必须映射到6大分类
> 3. 格式：`- YYYY-MM-DD | [收入/支出] | [主分类] | #子标签 | ￥金额 | 原始输入`
> 4. 工资默认 ￥3,100，日期为该月 1 日；禁止用 #日结补录 记工资
> 5. 禁止收入与支出混在同一区块
> 6. 记账后运行 `python scripts/recalc.py --update`
> 7. 季度复盘在3/6/9/12月后生成

---

## 📊 {year}年度总览

| 指标 | 数值 |
|------|------|
| 年度总支出 | ￥0.00 |
| 年度总收入 | ￥0.00 |
| 年度净结余 | ￥0.00 |
| 月均支出 | ￥0.00 |
| 支出占收入 | 0% |

### 分类支出结构（全年）
- [生存基线]：￥0.00（0%）
- [精力与健康维护]：￥0.00（0%）
- [杠杆与生产力]：￥0.00（0%）
- [资产与储备]：￥0.00（0%）
- [弹性消耗]：￥0.00（0%）

---

""" + "".join(month_block(f"{m:02d}") for m in range(1, 13)) + """--- EOF ---
"""

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(template)

    print(f"✅ 已创建: {filepath}")
    print(f"📖 请编辑 {year}.md 开始记账")
    return True


def archive_year(year: int):
    """归档指定年份（标记为archived）"""
    base_dir = Path(__file__).parent.parent
    filepath = base_dir / f"{year}.md"

    if not filepath.exists():
        print(f"⚠️ 文件不存在: {filepath}")
        return False

    content = filepath.read_text(encoding='utf-8')
    content = content.replace('status: active', 'status: archived')
    content = content.replace('status: template', 'status: archived')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"📦 已归档: {filepath}")
    return True


def activate_year(year: int):
    """激活指定年份（标记为active，并归档其他active年份）"""
    base_dir = Path(__file__).parent.parent

    # 先归档所有当前active的年份
    for md_file in base_dir.glob("*.md"):
        if md_file.name in ["README.md", "MEMORY.md", "SYSTEM.md"]:
            continue
        content = md_file.read_text(encoding='utf-8')
        if 'status: active' in content:
            old_year = md_file.stem
            archive_year(int(old_year))

    # 激活目标年份
    filepath = base_dir / f"{year}.md"
    if not filepath.exists():
        print(f"⚠️ 文件不存在: {filepath}，请先创建模板")
        return False

    content = filepath.read_text(encoding='utf-8')
    content = content.replace('status: template', 'status: active')
    content = content.replace('status: archived', 'status: active')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 已激活: {filepath}")
    print(f"📝 现在可以开始记账了")
    return True


def main():
    if len(sys.argv) < 2:
        # 自动创建下一年模板
        current_year = datetime.now().year
        next_year = current_year + 1
        print(f"未指定年份，自动创建 {next_year} 年度模板")
        create_year_template(next_year)
    elif sys.argv[1] == '--activate':
        # 激活指定年份: python new_year.py --activate 2027
        if len(sys.argv) < 3:
            print("用法: python new_year.py --activate <年份>")
            return
        year = int(sys.argv[2])
        activate_year(year)
    elif sys.argv[1] == '--archive':
        # 归档指定年份: python new_year.py --archive 2026
        if len(sys.argv) < 3:
            print("用法: python new_year.py --archive <年份>")
            return
        year = int(sys.argv[2])
        archive_year(year)
    else:
        year = int(sys.argv[1])
        create_year_template(year)


if __name__ == '__main__':
    main()
