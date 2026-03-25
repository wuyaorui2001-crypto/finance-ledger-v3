# MEMORY - 项目复盘记录

> 账本项目的详细变更历史和问题记录，按时间线组织

---

## 2026-03-18 | 添加自动同步工作流

**背景**：统一 thoughts 和 finance-ledger 的工作流，都使用 auto-sync.py 自动同步

**执行内容**：
1. 创建 `auto-sync.py` 自动同步脚本
2. 更新 `SYSTEM.md` 添加自动同步工作流程
3. 脚本功能：
   - 自动校验数据格式
   - 自动更新多年度分析
   - 自动生成可视化报表
   - 自动提交并推送到GitHub
   - GitHub Actions 自动部署

**使用方式**：
```
用户记账 → Agent记录 → 运行 auto-sync.py → 自动部署
```

---

## 2025-03-17 | 账本结构优化完成

**背景**：原始账本使用单文件存储，长期会导致性能问题
**执行内容**：
1. 创建优化版目录结构 `finance-ledger-v3-optimized/`
2. 将2026年历史数据迁移到 `2026.md`
3. 创建 `2027.md` 模板文件
4. 编写自动化脚本（validate.py, new_year.py, backup.sh）

**通用规则沉淀**：
- 已抽象为 PATTERN-001（数据分片）
- 已抽象为 PATTERN-004（跨平台脚本）

---

## 2025-03-17 | 建立复盘分级沉淀机制

**背景**：项目复盘应该记录在哪里？agentspace还是项目本地？
**决策过程**：
- 项目特定细节 → MEMORY.md（本文件）
- 通用可复用规则 → agentspace/02-PATTERNS.md
- 及时沉淀，不等3个项目积累

**执行内容**：
1. 更新 agentspace/02-MEMORY/00-CORE.md 添加复盘规则
2. 创建 agentspace/02-MEMORY/02-PATTERNS.md
3. 创建 agentspace/02-MEMORY/03-ARCHIVE/ 分类目录
4. 为账本项目创建 SYSTEM.md（AI操作指南）

**通用规则沉淀**：
- 已抽象为 PATTERN-002（每个项目必须创建SYSTEM.md）
- 已抽象为 PATTERN-003（复盘必须分级沉淀）

---

## 2026-03-17 | 添加可迁移性说明

**背景**：需要确保项目符合agent-workspace PATTERN-005标准
**执行内容**：
1. 更新 SYSTEM.md 添加"可迁移性说明"章节
2. 明确迁移测试步骤和自检清单
3. 关联到通用规则 PATTERN-005

**通用规则沉淀**：
- 已抽象为 PATTERN-005（项目可迁移性设计标准）

## 2026-03-25 | 账本优化 v3.2 - 统一解析与配置

**背景**：团队讨论确定4个优化方案，需要执行并确保下一代Agent能无缝继承

**执行内容**：
1. 创建 `scripts/parser.py` - 统一解析模块
   - `parse_record(line)`: 解析单条记账记录
   - `parse_year_file(filepath)`: 解析年度文件
   - `get_current_year()`: 获取当前应记账年份
   - 遵循 PATTERN-006 元数据标记必须交叉验证原则

2. 创建 `scripts/config.py` - 集中配置
   - `CATEGORIES`: 六维主分类列表
   - `LEDGER_CATEGORIES`: 子标签到主分类的映射表
   - `YEAR_FILES_PATH`, `REPORTS_PATH` 等路径常量

3. 创建 `scripts/recalc.py` - 自动计算统计
   - 读取年度文件，根据流水明细计算各项统计
   - 支持 `--dry-run` 参数（只输出不写入）
   - 支持 `--update` 参数（实际更新文件）
   - 输出各月度面板数据 + 年度总览

4. 改造 `scripts/validate.py`
   - 新增 `--check-active` 参数：检查当前应记录哪个年份
   - 复用 parser.py 的解析函数

5. 更新 `SYSTEM.md`
   - 在"自动化工具"章节添加 parser.py/config.py/recalc.py 说明

**存量数据保护**：
- 2026.md 和 2027.md 原始数据只读不修改
- 备份位置：`C:\Users\wuyao\2026.md.bak` 和 `C:\Users\wuyao\2027.md.bak`

**同步策略**：
- auto-sync.py 改为每周定时+手动触发（本次不改动逻辑，只在文档说明）

## 待记录

- 后续遇到的问题和解决方案在此追加
