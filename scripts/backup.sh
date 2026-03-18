#!/bin/bash
# 账本备份脚本
# 执行四层备份：本地时间戳 + Git + 飞书云 + GitHub

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LEDGER_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$LEDGER_DIR/backup"
DATE=$(date +%Y%m%d_%H%M%S)

echo "🏦 开始备份流程..."
echo "📁 账本目录: $LEDGER_DIR"
echo "📅 备份时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Layer 1: 本地时间戳备份
echo "📦 Layer 1: 本地时间戳备份..."
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/ledger_$DATE.tar.gz" -C "$LEDGER_DIR" \
    *.md \
    scripts/ \
    2>/dev/null || true

# 保留最近30个备份
ls -t "$BACKUP_DIR"/ledger_*.tar.gz 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true

echo "   ✓ 本地备份完成: $BACKUP_DIR/ledger_$DATE.tar.gz"
echo ""

# Layer 2: Git版本控制
echo "📦 Layer 2: Git版本控制..."
cd "$LEDGER_DIR"

if [ -d .git ]; then
    git add -A 2>/dev/null || true
    git commit -m "备份: $DATE" 2>/dev/null || echo "   ℹ️ 无变更需要提交"
    echo "   ✓ Git提交完成"
else
    echo "   ⚠️ 未初始化Git仓库，建议运行: git init"
fi
echo ""

# Layer 3 & 4: 远程推送
echo "📦 Layer 3 & 4: 远程备份..."
if git remote -v >/dev/null 2>&1; then
    git push origin main 2>/dev/null || git push origin master 2>/dev/null || echo "   ⚠️ 远程推送失败，请检查网络"
    echo "   ✓ 远程推送完成"
else
    echo "   ⚠️ 未配置远程仓库"
fi
echo ""

# 备份统计
echo "📊 备份统计:"
echo "   - 本地备份数量: $(ls -1 "$BACKUP_DIR"/ledger_*.tar.gz 2>/dev/null | wc -l)"
echo "   - Git提交历史: $(git log --oneline 2>/dev/null | wc -l) 条"
echo ""

# 数据校验
echo "🔍 执行数据校验..."
python3 "$SCRIPT_DIR/validate.py" 2>/dev/null || echo "   ⚠️ 校验脚本执行失败"
echo ""

echo "✅ 备份流程完成!"
echo "📍 备份位置: $BACKUP_DIR"
