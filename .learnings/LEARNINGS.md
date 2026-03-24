# 学习记录 - LEARNINGS

> 此文件记录 finance-ledger 项目专属的学习教训
> 已提炼规则 → REFINED.md

---

## [LRN-20250317-001] 账本记账年份验证机制

**记录时间**: 2025-03-17T21:45:00+08:00
**优先级**: high
**状态**: refined
**领域**: workflow
**来源**: user_feedback

### 摘要
记账时必须验证实际日期，不能仅依赖文件的`status`字段

### 根本原因
1. 过度依赖元数据标记，未做交叉验证
2. 发现2027.md空白但status=active时没有警觉
3. 没有检查2026.md是否已有今天的记录

### 解决方案
**记账前必须执行以下检查**:
1. 确定当前实际日期（或询问用户）
2. 选择对应年份的文件（如2026.md）
3. 检查该文件当月是否有记录
4. 追加新记录到正确年份

### 提炼状态
✅ 已提炼至 REFINED.md RULE-001

### 元数据
- Pattern-Key: workflow.ledger_year_verification
- Related-Errors: ERR-20250317-001

---

## [LRN-20250317-002] 账本统计数据同步更新

**记录时间**: 2025-03-17T21:50:00+08:00
**优先级**: medium
**状态**: refined
**领域**: workflow
**来源**: self_reflection

### 摘要
记账后必须同步更新三个层级的统计数据

### 详细
添加新记录后，需要更新：
1. **当月流水明细** - 追加新记录
2. **当月数据面板** - 更新总支出、净结余、占比
3. **年度总览** - 更新年度总支出、月均、分类结构

### 更新顺序
```
流水明细 → 当月面板 → 年度总览
```

### 校验
更新后运行 `python scripts/validate.py` 确保格式正确

### 提炼状态
✅ 已提炼至 REFINED.md RULE-002

### 元数据
- Pattern-Key: workflow.ledger_stats_sync

---

*finance-ledger 项目专属教训 | 已归档至 REFINED.md*
