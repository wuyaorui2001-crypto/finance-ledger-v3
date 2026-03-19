# SYSTEM - 冰美式财务账本 AI操作指南

> 本文件是AI接手账本项目的必读指南，包含标准操作流程和强制规则

---

## 1. 项目一句话定义

**个人财务管理的结构化账本系统，采用六维分类体系和AI原生设计，支持10年以上长期记账。**

---

## 2. AI接手后的标准SOP流程

### 场景A：日常记账
1. 读取当前年度文件（如 `2027.md`）
2. 找到当前月份区块
3. 按格式追加新记录到"当月流水明细"
4. 更新"当月数据面板"统计数字
5. 运行 `python auto-sync.py` 自动同步到GitHub
6. GitHub Actions 自动更新可视化仪表盘

### 场景B：创建新年度
1. 运行 `python scripts/new_year.py 20XX`
2. 新年度文件自动生成，包含12个月模板
3. 更新 `README.md` 中的年度索引
4. 运行 `python scripts/analyze.py` 更新多年度分析报告

### 场景C：跨年度查询
1. 查看 `INDEX.md` 获取多年度汇总统计
2. 使用 `python scripts/analyze.py` 重新生成分析报告
3. 包含：年度对比、分类结构、10年趋势

### 场景D：数据备份
1. 运行 `bash scripts/backup.sh`
2. 或使用Git提交
3. GitHub Actions 自动更新可视化仪表盘

---

## 3. 强制规则检查清单

| 检查项 | 规则 | 错误后果 |
|-------|------|---------|
| 主分类 | 必须映射到6大分类之一，禁止自创 | 分类体系混乱 |
| 格式 | `- 日期 \| 类型 \| [分类] \| #子标签 \| ￥金额 \| 原始输入` | AI解析失败 |
| 日期 | 必须与文件名年份一致 | 年度统计错误 |
| 修改历史 | 禁止修改或删除历史记录 | 数据不可信 |
| EOF位置 | 所有数据必须在 `--- EOF ---` 之前 | 数据丢失 |

**六维主分类（禁止更改）：**
1. 生存基线
2. 精力与健康维护
3. 杠杆与生产力
4. 资产与储备
5. 弹性消耗
6. 资金流入

---

## 4. 常见场景处理示例

### 示例1：记录日常支出
```
用户输入：午饭25
AI输出：- 2027-03-11 | 支出 | [生存基线] | #午饭 | ￥25.00 | 午饭25
```

### 示例2：记录工资收入
```
用户输入：3月工资5000
AI输出：- 2027-03-07 | 收入 | [资金流入] | #工资 | ￥5,000.00 | 3月工资5000
```

### 示例3：不确定分类
```
用户输入：买书花了50
AI判断：书籍属于自我提升，归类到 [杠杆与生产力]
AI输出：- 2027-03-11 | 支出 | [杠杆与生产力] | #书籍 | ￥50.00 | 买书花了50
```

---

## 5. 项目特定教训（错题本）

| 日期 | 问题 | 教训 |
|-----|------|------|
| 2025-03-17 | 单文件过大影响性能 | 按年分文件，见PATTERN-001 |
| 2025-03-17 | 格式错误导致解析失败 | 必须运行validate.py校验 |
| 2025-03-18 | 多年度统计困难 | 使用analyze.py生成INDEX.md |

---

## 6. 10年记账支持说明

### 设计容量
- **单文件大小**: 年均 ~15KB，10年 ~150KB（可接受）
- **记录数**: 年均 ~150条，10年 ~1,500条
- **查询性能**: 按年分片，打开单个年度文件即可

### 多年度管理
| 文件 | 用途 |
|------|------|
| `2XXX.md` | 各年度详细账本 |
| `INDEX.md` | 多年度汇总分析（自动生成） |
| `README.md` | 年度索引和快速链接 |

### 自动化工具
```bash
# 创建新年度
python scripts/new_year.py 2030

# 更新多年度分析
python scripts/analyze.py

# 生成可视化报表
python scripts/visualize.py

# 校验所有年度
python scripts/validate.py
```

---

## 7. 关联的通用规则

- **PATTERN-001**: 长期数据存储必须支持分片
- **PATTERN-004**: 自动化脚本优先使用Python，避免emoji

## 7. 可迁移性说明 + GitHub 集成

**符合 agent-workspace PATTERN-005 标准**

### GitHub 仓库
- **账本仓库**: https://github.com/wuyaorui2001-crypto/finance-ledger-v3
- **核心资产库**: https://github.com/wuyaorui2001-crypto/agentworkspace

### 恢复方法
```bash
# 克隆仓库
git clone https://github.com/wuyaorui2001-crypto/finance-ledger-v3.git
cd finance-ledger-v3

# 读取 SYSTEM.md → 理解SOP → 开始工作
cat SYSTEM.md
```

**可视化仪表盘**: https://wuyaorui2001-crypto.github.io/finance-ledger-v3/

### 迁移测试
复制本目录到新设备后，新Agent应能：
1. 读取 `SYSTEM.md` → 理解六维分类和记账规则
2. 读取 `README.md` → 理解项目结构和年度索引
3. 无需用户解释即可开始记账

### 自检清单
- [x] 一句话定义：个人财务管理的结构化账本系统
- [x] AI操作指南：SYSTEM.md 包含完整SOP和场景示例
- [x] 文件结构自解释：YYYY.md + scripts/ + README索引
- [x] 示例存在：2026.md 展示标准格式
- [x] 格式校验：scripts/validate.py 确保数据质量

### 迁移步骤
1. 复制整个 `finance-ledger-v3-optimized/` 目录
2. 新Agent读取 `SYSTEM.md` → 理解10年记账设计
3. 读取 `INDEX.md` → 查看多年度汇总
4. 开始记账

## 8. 自动同步工作流

### 完整流程

```
用户记账 → AI记录到 YYYY.md → 运行 auto-sync.py → 推送到GitHub → GitHub Actions部署仪表盘
```

### Agent操作步骤

当用户记账后：

1. **记录账单**
   - 读取当前年度文件
   - 按格式追加记录
   - 更新当月数据面板

2. **自动同步**（每次记录后执行）
   ```bash
   python auto-sync.py
   ```
   
   此脚本会自动：
   - 校验数据格式 (`scripts/validate.py`)
   - 更新多年度分析 (`scripts/analyze.py`)
   - 生成可视化报表 (`scripts/visualize.py`)
   - 提交所有更改到 Git
   - 推送到 GitHub
   - GitHub Actions 自动部署到 Pages

3. **通知用户**
   - 告知记账已完成
   - 提供可视化仪表盘链接
   - 说明部署等待时间（1-2分钟）

### 手动同步（备用）

如果自动同步失败，可手动执行：

```bash
# 进入项目目录
cd "D:\Me\u0026AI\Project\finance-ledger-v3-optimized"

# 运行同步脚本
python auto-sync.py
```

### 查看可视化仪表盘

- **在线地址**: https://wuyaorui2001-crypto.github.io/finance-ledger-v3/
- **部署状态**: https://github.com/wuyaorui2001-crypto/finance-ledger-v3/actions

---

## 9. 同步规则更新（2026-03-19）

### 双模式同步机制

| 模式 | 触发条件 | 执行方式 |
|-----|---------|---------|
| **定期同步** | 每周日 12:00 | cron定时任务自动执行 |
| **手动同步** | 用户指令 | 立即执行 |

### 手动同步指令

用户输入以下任一指令时，立即执行同步：
- "上传项目"
- "同步"
- "推送GitHub"

### 数据安全原则

- **本地优先**: 所有数据先写入本地文件，同步是可选的、可延迟的
- **定期批量**: 默认每周日批量同步，减少API调用和无效提交
- **即时备份**: 重要更改可手动触发同步

### 分支支持

同时支持 `main` 和 `master` 分支推送（优先main，失败则尝试master）

---

*最后更新：2026-03-19*
*版本：v3.3*
