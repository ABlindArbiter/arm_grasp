#!/usr/bin/env bash
# git_helper.sh —— 给「只在最后传一次」的人用的最小 Git 包装
# 用法：./git_helper.sh <命令> [参数]
# 依赖：git 2.28+（没有也能跑，init 会退化为 git init）
set -euo pipefail

C_OK="\033[32m"; C_WARN="\033[33m"; C_ERR="\033[31m"; C_DIM="\033[2m"; C_END="\033[0m"
ok()   { printf "${C_OK}%s${C_END}\n" "$*"; }
warn() { printf "${C_WARN}%s${C_END}\n" "$*"; }
err()  { printf "${C_ERR}%s${C_END}\n" "$*" >&2; }
dim()  { printf "${C_DIM}%s${C_END}\n" "$*"; }

need_repo() {
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    err "当前目录不是 git 仓库。先运行：./git_helper.sh init"
    exit 1
  fi
}

has_remote() {
  [ -n "$(git remote 2>/dev/null | head -n1)" ]
}

current_branch() {
  git branch --show-current 2>/dev/null || echo main
}

write_gitignore() {
  if [ -f .gitignore ]; then
    dim ".gitignore 已存在，跳过"
    return
  fi
  cat > .gitignore <<'EOF'
# ---- Python ----
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
env/
.pytest_cache/
.mypy_cache/
.ipynb_checkpoints/

# ---- C / 嵌入式 ----
build/
Debug/
Release/
*.o
*.d
*.elf
*.bin
*.hex
*.map
*.su

# ---- ROS2 ----
install/
log/
build/
*.bag
*.db3
*.mcap
*.yaml.bak

# ---- 数据 / 模型 / 大文件（不进 git）----
data/
datasets/
logs/
*.csv
*.npz
*.npy
*.onnx
*.pt
*.pth
*.engine
*.mp4
*.avi
*.mov

# ---- 图片：默认忽略，但 docs/media 里的保留 ----
*.png
*.jpg
*.jpeg
*.gif
!docs/media/
!docs/media/*

# ---- 密钥 / 环境 ----
.env
*.key
*.pem
secrets.yaml

# ---- 编辑器 / 系统 ----
.vscode/
.idea/
.DS_Store
Thumbs.db
EOF
  ok "已生成 .gitignore"
}

cmd_init() {
  write_gitignore

  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    warn "当前目录已经是 git 仓库，跳过 init"
  else
    if git init -b main >/dev/null 2>&1; then
      :
    else
      git init >/dev/null
      git symbolic-ref HEAD refs/heads/main 2>/dev/null || true
    fi
    ok "已初始化仓库（分支 main）"
  fi

  mkdir -p docs/media firmware/stm32 pc/arm pc/vision pc/grasp pc/ros2_bridge \
           pc/config pc/tests sim tools scripts
  for d in docs/media firmware/stm32 pc/arm pc/vision pc/grasp pc/ros2_bridge \
           pc/config pc/tests sim scripts; do
    [ -f "$d/.gitkeep" ] || : > "$d/.gitkeep"
  done

  [ -f docs/hardware.md ]    || printf '# 硬件\n\n> 接线图、上电流程、盘点结论。\n' > docs/hardware.md
  [ -f docs/dh_table.md ]    || printf '# DH 表\n\n> 坐标系简图 + DH 表 + J5 轴线结论（roll/pitch）。\n' > docs/dh_table.md
  [ -f docs/calibration.md ] || printf '# 手眼标定\n\n> 方法、采集组数、残差、矩阵、验证结果。\n' > docs/calibration.md
  [ -f docs/debug_log.md ]   || printf '# 调试日志\n\n> 格式：问题 → 现象 → 排查 → 根因 → 修复\n' > docs/debug_log.md
  [ -f README.md ] || cat > README.md <<'EOF'
# arm-grasp

5 自由度舵机臂 + ZED-M 的视觉抓取项目。

## 架构

```
PC（视觉 / 抓取 / 运动学） --USB--> STM32（安全转发层） --> ZLink --> 舵机
                ^
                └── ZED-M
```

## 快速开始

（待填：环境依赖、启动命令）

## 结果

（待填：成功率、误差表、视频链接）

## 目录

- `pc/` 上位机
- `firmware/` STM32
- `sim/` PyBullet
- `docs/` 文档与调试记录
EOF

  git add -A
  if git diff --cached --quiet; then
    dim "没有需要提交的改动"
  else
    git commit -m "chore: 初始化项目骨架" >/dev/null
    ok "首次提交完成"
  fi
  dim "下一步：./git_helper.sh remote <仓库地址>"
}

cmd_save() {
  need_repo
  local msg="${1:-}"
  if [ -z "$msg" ]; then
    err "缺少提交信息。例：./git_helper.sh save \"feat(ik): 解析解跑通\""
    exit 1
  fi
  git add -A
  if git diff --cached --quiet; then
    dim "没有改动，无需提交"
    return
  fi
  git commit -m "$msg" >/dev/null
  ok "已提交：$msg"
  dim "本地存档完成，云端备份用：./git_helper.sh sync"
}

cmd_sync() {
  need_repo
  if ! has_remote; then
    err "还没有远端仓库。先运行：./git_helper.sh remote <仓库地址>"
    exit 1
  fi
  local br; br="$(current_branch)"
  if git rev-parse --verify "origin/$br" >/dev/null 2>&1; then
    dim "拉取远端并变基…"
    git pull --rebase --autostash origin "$br" || { err "拉取失败，先看 git status"; exit 1; }
  fi
  if git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1; then
    git push
  else
    git push -u origin "$br"
  fi
  ok "已同步到远端（$br）"
}

cmd_tag() {
  need_repo
  local name="${1:-}"
  if [ -z "$name" ]; then
    err "缺少标签名。例：./git_helper.sh tag w10-pass"
    exit 1
  fi
  git tag -a "$name" -m "$name" 2>/dev/null || { err "标签已存在：$name"; exit 1; }
  ok "已打标签：$name"
  if has_remote; then
    git push origin "$name" >/dev/null
    ok "标签已推送"
  fi
}

cmd_undo() {
  need_repo
  if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
    err "还没有任何提交"
    exit 1
  fi
  local subj; subj="$(git log -1 --pretty=%s)"
  git reset --soft HEAD~1
  ok "已撤销提交（改动保留在工作区）：$subj"
  warn "如果这个提交已经 push 过，撤销后要用 --force 才能推，谨慎操作。"
}

cmd_back() {
  need_repo
  local f="${1:-}"
  if [ -z "$f" ]; then
    err "缺少文件名。例：./git_helper.sh back pc/arm/ik.py"
    exit 1
  fi
  printf "确认丢弃 %s 的未提交改动？[y/N] " "$f"
  read -r ans
  if [ "$ans" = "y" ] || [ "$ans" = "Y" ]; then
    git checkout -- "$f"
    ok "已还原：$f"
  else
    dim "已取消"
  fi
}

cmd_remote() {
  need_repo
  local url="${1:-}"
  if [ -z "$url" ]; then
    err "缺少仓库地址。例：./git_helper.sh remote git@github.com:you/arm-grasp.git"
    exit 1
  fi
  if has_remote; then
    git remote set-url origin "$url"
  else
    git remote add origin "$url"
  fi
  local br; br="$(current_branch)"
  git push -u origin "$br"
  ok "已连接远端并推送（$br）"
}

cmd_status() {
  need_repo
  git status -sb
  echo
  git diff --stat
}

cmd_log() {
  need_repo
  git log --oneline --graph --decorate -20
}

cmd_help() {
  cat <<'EOF'
git_helper.sh —— 最小 Git 包装

用法：./git_helper.sh <命令> [参数]

  init                 建目录骨架 + .gitignore + 首次提交
  remote <URL>         连接远端仓库并首次推送
  save "说明"          暂存全部改动并提交（最常用）
  sync                 拉取远端（变基）并推送
  tag <名字>           打里程碑标签并推送
  undo                 撤销最近一次提交（改动保留）
  back <文件>          丢弃某个文件的未提交改动
  status               简洁状态
  log                  最近 20 条图形化历史

例：
  ./git_helper.sh init
  ./git_helper.sh remote git@github.com:me/arm-grasp.git
  ./git_helper.sh save "feat(ik): 解析解支持肘上/肘下"
  ./git_helper.sh sync
EOF
}

main() {
  local cmd="${1:-help}"
  shift || true
  case "$cmd" in
    init)    cmd_init "$@" ;;
    remote)  cmd_remote "$@" ;;
    save)    cmd_save "$@" ;;
    sync)    cmd_sync "$@" ;;
    tag)     cmd_tag "$@" ;;
    undo)    cmd_undo "$@" ;;
    back)    cmd_back "$@" ;;
    status)  cmd_status "$@" ;;
    log)     cmd_log "$@" ;;
    help|-h|--help) cmd_help ;;
    *) err "未知命令：$cmd"; echo; cmd_help; exit 1 ;;
  esac
}

main "$@"
