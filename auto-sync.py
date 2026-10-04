#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finance Ledger 自动同步脚本
Agent记账后调用此脚本自动推送到GitHub

多端记账（本机 / 云端 Agent）时，推送前会先拉取远程，
按流水行合并年度账本，再重算面板与报表后提交。
"""

import os
import re
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

# 设置环境变量避免编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
from ledger_merge import merge_year_text  # noqa: E402

GENERATED_FILES = {'INDEX.md', 'reports/data.json', 'reports/index.html'}
YEAR_FILE_RE = re.compile(r'^\d{4}\.md$')
DEFAULT_PROXY = 'http://127.0.0.1:7890'
MAX_PUSH_ATTEMPTS = 3


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


def is_cache_file(path):
    return '__pycache__/' in path or path.endswith('.pyc')


def git_show(project_dir, rev, path):
    """读取某个提交里的文件内容；不存在返回 None"""
    result = subprocess.run(
        ['git', 'show', f'{rev}:{path}'],
        cwd=project_dir,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    return result.stdout if result.returncode == 0 else None


def proxy_url():
    """本机代理可用时返回代理地址（LEDGER_GIT_PROXY 可覆盖，设为空则禁用）"""
    url = os.environ.get('LEDGER_GIT_PROXY', DEFAULT_PROXY)
    if not url:
        return None
    parsed = urlparse(url)
    try:
        with socket.create_connection((parsed.hostname, parsed.port), timeout=0.5):
            return url
    except OSError:
        return None


def run_git_network(args, cwd):
    """联网的 git 命令：本机代理可用时先走代理，失败再直连"""
    proxy = proxy_url()
    if proxy:
        ok, out, err = run_command(
            f'git -c http.proxy={proxy} -c https.proxy={proxy} {args}', cwd=cwd
        )
        if ok:
            return ok, out, err
    return run_command(f'git {args}', cwd=cwd)


def current_branch(project_dir):
    ok, out, _ = run_command('git rev-parse --abbrev-ref HEAD', cwd=project_dir)
    return out.strip() if ok else 'main'


def remote_has_new_commits(project_dir, upstream):
    ok, _, _ = run_command(f'git rev-parse --verify {upstream}', cwd=project_dir)
    if not ok:
        return False
    is_ancestor, _, _ = run_command(
        f'git merge-base --is-ancestor {upstream} HEAD', cwd=project_dir
    )
    return not is_ancestor


def local_ahead(project_dir, upstream):
    ok, out, _ = run_command(f'git rev-list --count {upstream}..HEAD', cwd=project_dir)
    return ok and out.strip() not in ('', '0')


def sync_with_remote(project_dir, branch, dry_run=False):
    """
    拉取远程；远程有新提交时，把本地对年度账本的改动按流水行叠加到远程版本上。
    返回 False 表示需要人工处理，不应继续提交。
    """
    upstream = f'origin/{branch}'
    print("[INFO] 拉取远程最新账本...")
    ok, _, stderr = run_git_network(f'fetch origin {branch}', cwd=project_dir)
    if not ok:
        print("[WARN] 拉取远程失败，跳过合并（若远程有新记录，稍后推送会被拒绝）")
        return True

    if not remote_has_new_commits(project_dir, upstream):
        print("[OK] 远程没有新记录")
        return True

    print("[INFO] 远程有其他端的新记录，开始合并...")
    if dry_run:
        print("[INFO] [DRY-RUN] 跳过合并")
        return True

    _, base, _ = run_command(f'git merge-base HEAD {upstream}', cwd=project_dir)
    base = base.strip()
    _, diff_out, _ = run_command(f'git diff --name-only {base}', cwd=project_dir)
    changed = {p.strip() for p in diff_out.splitlines() if p.strip()}

    year_files = sorted(p for p in changed if YEAR_FILE_RE.match(p))
    others = sorted(
        p for p in changed
        if p not in GENERATED_FILES and p not in year_files and not is_cache_file(p)
    )
    if others:
        print("[ERROR] 本地还改了账本以外的文件，无法自动合并，请先手动处理：")
        for p in others:
            print(f"        {p}")
        return False

    _, stash_sha, _ = run_command('git stash create', cwd=project_dir)
    backup_sha = stash_sha.strip() or 'HEAD'
    backup_ref = f"refs/ledger-backup/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    run_command(f'git update-ref {backup_ref} {backup_sha}', cwd=project_dir)
    print(f"[INFO] 本地改动已备份到 {backup_ref}")

    merged_files = {}
    for path in year_files:
        local_file = project_dir / path
        ours = local_file.read_text(encoding='utf-8') if local_file.exists() else None
        base_text = git_show(project_dir, base, path) or ''
        theirs = git_show(project_dir, upstream, path)
        merged, added, removed, suspects = merge_year_text(base_text, ours, theirs)
        merged_files[path] = merged
        print(f"[INFO] {path}: 叠加本地新增 {added} 条、删除 {removed} 条")
        for record in suspects:
            print(f"[WARN] 疑似两端重复记账，请核对: {record}")

    ok, _, stderr = run_command(f'git reset --hard {upstream}', cwd=project_dir)
    if not ok:
        print(f"[ERROR] 切换到远程版本失败: {stderr.strip()}")
        return False

    for path, merged in merged_files.items():
        if merged is None:
            (project_dir / path).unlink(missing_ok=True)
        else:
            with open(project_dir / path, 'w', encoding='utf-8') as f:
                f.write(merged)

    print("[OK] 合并完成")
    return True


def rebuild_outputs(project_dir):
    """校验 → 重算面板 → 多年度分析 → 可视化"""
    print("[INFO] 校验数据格式...")
    success, _, _ = run_command("python scripts/validate.py", cwd=project_dir)
    if not success:
        print("[ERROR] 数据校验失败，请检查格式")
        return False
    print("[OK] 数据校验通过")

    print("[INFO] 重算统计数据面板...")
    success, _, _ = run_command("python scripts/recalc.py --update", cwd=project_dir)
    print("[OK] 面板重算完成" if success else "[WARN] 面板重算失败，继续同步...")

    print("[INFO] 更新多年度分析...")
    success, _, _ = run_command("python scripts/analyze.py", cwd=project_dir)
    print("[OK] 分析完成" if success else "[WARN] 分析脚本执行失败，继续同步...")

    print("[INFO] 生成可视化报表...")
    success, _, _ = run_command("python scripts/visualize.py", cwd=project_dir)
    print("[OK] 报表生成完成" if success else "[WARN] 可视化脚本执行失败，继续同步...")
    return True


def commit_if_changed(project_dir):
    success, stdout, _ = run_command("git status --porcelain", cwd=project_dir)
    if not success:
        print("[ERROR] Git状态检查失败")
        return None
    if not stdout.strip():
        return False

    print("[INFO] 添加更改到Git...")
    success, _, _ = run_command("git add .", cwd=project_dir)
    if not success:
        print("[ERROR] Git add 失败")
        return None

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"自动同步: 更新账本记录 @ {timestamp}"
    print("[INFO] 提交更改...")
    success, _, _ = run_command(f'git commit -m "{commit_msg}"', cwd=project_dir)
    if not success:
        print("[ERROR] Git commit 失败")
        return None
    return True


def sync_to_github(dry_run=False):
    """同步到GitHub"""
    project_dir = Path(__file__).parent
    branch = current_branch(project_dir)
    upstream = f'origin/{branch}'

    print("[INFO] 开始同步 Finance Ledger 到 GitHub...")
    if dry_run:
        print("[INFO] [DRY-RUN 模式] 不会执行任何更改")

    for attempt in range(1, MAX_PUSH_ATTEMPTS + 1):
        if not sync_with_remote(project_dir, branch, dry_run=dry_run):
            return False

        if dry_run:
            _, stdout, _ = run_command("git status --porcelain", cwd=project_dir)
            print(f"[INFO] [DRY-RUN] 以下文件将被提交:\n{stdout}" if stdout.strip()
                  else "[INFO] 没有需要同步的更改")
            return True

        if not rebuild_outputs(project_dir):
            return False

        print("[INFO] 检查Git状态...")
        committed = commit_if_changed(project_dir)
        if committed is None:
            return False
        if not committed and not local_ahead(project_dir, upstream):
            print("[INFO] 没有需要同步的更改")
            return True

        print("[INFO] 推送到GitHub...")
        success, _, stderr = run_git_network(f'push origin {branch}', cwd=project_dir)
        if success:
            print("[OK] 同步完成!")
            print("[INFO] 查看可视化仪表盘: https://wuyaorui2001-crypto.github.io/finance-ledger-v3/")
            print("[INFO] 部署需要1-2分钟，请稍后刷新查看")
            return True

        run_git_network(f'fetch origin {branch}', cwd=project_dir)
        if remote_has_new_commits(project_dir, upstream) and attempt < MAX_PUSH_ATTEMPTS:
            print("[WARN] 推送期间远程又有新记录，重新合并后再推送...")
            continue

        print(f"[ERROR] Git push 失败: {stderr.strip()[-300:]}")
        print("[INFO] 本地提交已保留，下次运行 auto-sync.py 会自动补推")
        return False

    return False


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    success = sync_to_github(dry_run=dry_run)
    sys.exit(0 if success else 1)
