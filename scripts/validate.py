#!/usr/bin/env python3
"""
账本数据格式校验脚本
验证每条记录是否符合规范格式
"""

import re
import sys
from pathlib import Path

# 六维主分类
VALID_CATEGORIES = [
    "生存基线",
    "精力与健康维护",
    "杠杆与生产力",
    "资产与储备",
    "弹性消耗",
    "资金流入"
]

# 记账记录正则
RECORD_PATTERN = re.compile(
    r'^- (\d{4}-\d{2}-\d{2})\s+'  # 日期
    r'\|\s*(收入|支出)\s*\|\s*'   # 类型
    r'\[([^\]]+)\]\s*\|\s*'      # 主分类
    r'(#[^\s|]+)\s*\|\s*'         # 子标签
    r'[￥¥]([\d,]+\.?\d*)\s*\|\s*'  # 金额
    r'(.+)$'                      # 原始输入
)


def validate_year_file(year: int) -> tuple[bool, list[str]]:
    """验证年度账本文件"""
    filepath = Path(__file__).parent.parent / f"{year}.md"

    if not filepath.exists():
        return False, [f"文件不存在: {filepath}"]

    errors = []
    warnings = []
    line_num = 0
    record_count = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line_num += 1
            line = line.rstrip()

            # 跳过非记录行
            if not line.startswith('- 20'):
                continue

            record_count += 1
            match = RECORD_PATTERN.match(line)

            if not match:
                errors.append(f"第{line_num}行: 格式错误 - {line[:50]}...")
                continue

            date, record_type, category, subtag, amount, original = match.groups()

            # 验证日期格式
            try:
                year_in_date = int(date.split('-')[0])
                if year_in_date != year:
                    warnings.append(f"第{line_num}行: 日期年份({year_in_date})与文件名({year})不符")
            except:
                errors.append(f"第{line_num}行: 日期解析失败")

            # 验证主分类
            if category not in VALID_CATEGORIES:
                errors.append(f"第{line_num}行: 无效主分类 '{category}'")

            # 验证子标签格式
            if not subtag.startswith('#'):
                errors.append(f"第{line_num}行: 子标签必须以#开头")

            # 验证金额
            try:
                amount_clean = amount.replace(',', '')
                float(amount_clean)
            except:
                errors.append(f"第{line_num}行: 金额格式错误 '{amount}'")

    # 生成报告
    report = []
    report.append(f"\n[{year}年度账本校验报告]")
    report.append("=" * 50)
    report.append(f"总记录数: {record_count}")
    report.append(f"错误数: {len(errors)}")
    report.append(f"警告数: {len(warnings)}")

    if errors:
        report.append("\n[错误]:")
        for error in errors[:10]:  # 只显示前10个错误
            report.append(f"  {error}")
        if len(errors) > 10:
            report.append(f"  ... 还有 {len(errors) - 10} 个错误")

    if warnings:
        report.append("\n[警告]:")
        for warning in warnings[:5]:
            report.append(f"  {warning}")

    if not errors and not warnings:
        report.append("\n[校验通过，数据格式正确]")

    return len(errors) == 0, report


def main():
    if len(sys.argv) > 1:
        # 验证指定年份
        year = int(sys.argv[1])
        success, report = validate_year_file(year)
        print('\n'.join(report))
        sys.exit(0 if success else 1)
    else:
        # 验证所有年度文件
        base_dir = Path(__file__).parent.parent
        year_files = sorted(base_dir.glob('[0-9][0-9][0-9][0-9].md'))

        all_success = True
        for filepath in year_files:
            year = int(filepath.stem)
            success, report = validate_year_file(year)
            print('\n'.join(report))
            if not success:
                all_success = False
            print()

        sys.exit(0 if all_success else 1)


if __name__ == '__main__':
    main()
