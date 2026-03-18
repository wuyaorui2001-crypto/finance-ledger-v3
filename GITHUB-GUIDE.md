# GitHub 集成指南

## 仓库信息

| 项目 | 仓库地址 | GitHub Pages |
|------|---------|-------------|
| finance-ledger | https://github.com/wuyaorui2001-crypto/finance-ledger-v3 | https://wuyaorui2001-crypto.github.io/finance-ledger-v3/ |

## 新设备/新Agent快速上手

### 1. 克隆仓库

```bash
git clone https://github.com/wuyaorui2001-crypto/finance-ledger-v3.git
```

### 2. 读取项目文档

```bash
cd finance-ledger-v3
cat SYSTEM.md
cat README.md
```

### 3. 开始工作

根据 SYSTEM.md 中的 SOP 流程开始记账。

---

## 日常同步流程

### 推送更改到 GitHub

```bash
git add .
git commit -m "记账更新: $(date +%Y-%m-%d)"
git push origin main
```

### 自动触发

推送后 GitHub Actions 会自动：
1. 运行 visualize.py 生成报表
2. 部署到 GitHub Pages

---

## 另一个 AI 接手流程

1. **克隆仓库** → 获取完整项目
2. **读取 SYSTEM.md** → 理解六维分类和记账规则
3. **读取 MEMORY.md** → 了解项目历史
4. **开始记账** → 按照 SOP 执行

---

*此文件帮助新 Agent 快速理解 GitHub 集成方案*
