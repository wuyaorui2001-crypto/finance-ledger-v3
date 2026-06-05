# AGENTS.md - 账本 Agent 入口

> Cursor / 其他 Agent 接手本项目时 **先读此文件**，再读 [SYSTEM.md](./SYSTEM.md)。

## 必读顺序

1. [AGENTS.md](./AGENTS.md)（本文件）
2. [SYSTEM.md](./SYSTEM.md)（完整 SOP）
3. 当前年度文件（如 [2026.md](./2026.md)）frontmatter 中的 `SYSTEM DIRECTIVE`

## 月度四段结构（v3.2+）

每个月份区块固定为：

```markdown
### MM月

#### 当月数据面板
（由 recalc.py 自动维护，勿手改数字）

#### 当月收入
- YYYY-MM-01 | 收入 | [资金流入] | #工资 | ￥3,100.00 | N月工资

#### 当月支出明细
- YYYY-MM-DD | 支出 | ...
```

## 记账路由

| 用户说什么 | 写到哪里 | 格式 |
|-----------|---------|------|
| 午饭19、咖啡30、晚饭40 | `#### 当月支出明细` | `\| 支出 \|` |
| N月工资、收入3100 | `#### 当月收入` | `\| 收入 \| [资金流入] \| #工资` |

**禁止：**

- 在支出明细里写收入
- 用 `#日结补录` 记工资
- 工资与花销混在同一区块

## 默认值

- 工资金额未指定：**￥3,100.00**
- 工资日期未指定：**该月 1 日**（如 `2026-06-01`）

## 记账后必做

```bash
python scripts/recalc.py --update
python scripts/visualize.py
# 或一键：
python auto-sync.py
```

## 校验

```bash
python scripts/validate.py
```

## 可视化

- 本地：`reports/index.html` + `reports/data.json`
- 线上：https://wuyaorui2001-crypto.github.io/finance-ledger-v3/

仪表盘含：总收入、净结余、支出占收入、每月收支双柱图。
