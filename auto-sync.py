#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finance Ledger 自动同步脚本
Agent记账后调用此脚本自动推送到GitHub
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

# 设置环境变量避免编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'

def run_command(cmd, cwd=None):
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def sync_to_github():
    """同步到GitHub"""
    project_dir = Path(__file__).parent
    
    print("[INFO] 开始同步 Finance Ledger 到 GitHub...")
    
    # 1. 校验数据格式
    print("[INFO] 校验数据格式...")
    success, stdout, stderr = run_command("python scripts/validate.py", cwd=project_dir)
    if not success:
        print(f"[ERROR] 数据校验失败，请检查格式")
        return False
    print("[OK] 数据校验通过")
    
    # 2. 更新多年度分析
    print("[INFO] 更新多年度分析...")
    success, stdout, stderr = run_command("python scripts/analyze.py", cwd=project_dir)
    if success:
        print("[OK] 分析完成")
    else:
        print("[WARN] 分析脚本执行失败，继续同步...")
    
    # 3. 生成可视化报表
    print("[INFO] 生成可视化报表...")
    success, stdout, stderr = run_command("python scripts/visualize.py", cwd=project_dir)
    if success:
        print("[OK] 报表生成完成")
    else:
        print("[WARN] 可视化脚本执行失败，继续同步...")
    
    # 4. 检查是否有更改
    print("[INFO] 检查Git状态...")
    success, stdout, stderr = run_command("git status --porcelain", cwd=project_dir)
    if not success:
        print(f"[ERROR] Git状态检查失败")
        return False
    
    if not stdout.strip():
        print("[INFO] 没有需要同步的更改")
        return True
    
    # 5. 添加所有更改
    print("[INFO] 添加更改到Git...")
    success, _, stderr = run_command("git add .", cwd=project_dir)
    if not success:
        print(f"[ERROR] Git add 失败")
        return False
    
    # 6. 提交
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"自动同步: 更新账本记录 @ {timestamp}"
    print(f"[INFO] 提交更改...")
    success, _, stderr = run_command(f'git commit -m "{commit_msg}"', cwd=project_dir)
    if not success:
        print(f"[ERROR] Git commit 失败")
        return False
    
    # 7. 推送到GitHub
    print("[INFO] 推送到GitHub...")
    success, stdout, stderr = run_command("git push origin main", cwd=project_dir)
    if not success:
        # 尝试 master 分支
        success, stdout, stderr = run_command("git push origin master", cwd=project_dir)
        if not success:
            print(f"[ERROR] Git push 失败")
            return False
    
    print("[OK] 同步完成!")
    print(f"[INFO] 查看可视化仪表盘: https://wuyaorui2001-crypto.github.io/finance-ledger-v3/")
    print(f"[INFO] 部署需要1-2分钟，请稍后刷新查看")
    return True

if __name__ == "__main__":
    success = sync_to_github()
    sys.exit(0 if success else 1)
