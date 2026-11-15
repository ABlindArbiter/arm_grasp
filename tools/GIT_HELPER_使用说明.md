# git_helper.sh 初学使用说明

> 给第一次用 GitHub 的人。只讲这个脚本，不用背 Git 命令。
> 一句话：**commit = 本地存档；push = 云端备份。** 脚本把这两件事拆成 `save` 和 `sync`。

---

## 0. 先记住三件事

| 你想干什么 | 命令 | 人话 |
|---|---|---|
| 存个档 | `./git_helper.sh save "说明"` | 把当前改动存到本地 |
| 备份到 GitHub | `./git_helper.sh sync` | 把本地存档推到云端 |
| 看现在什么状态 | `./git_helper.sh status` | 有没有没存的改动 |

**最容易错的一点：`save` 不等于上传。** `save` 只在本地；要 `sync` 才到 GitHub。

---

## 1. 你现在只需要这 5 个命令

```bash
cd ~/arm-grasp

./git_helper.sh status
./git_helper.sh save "feat(sim): 跑通 KUKA IK 画圆"
./git_helper.sh sync
```

- `status`：看改了什么、有没有没跟踪的文件。
- `save "说明"`：把所有改动存成一个 commit。
- `sync`：先拉云端，再推本地；每天结束/每周日用。

---

## 2. 第一次配置（如果你从零开始）

你现在的仓库已经配好了，这一段可以跳过；换电脑时再看。

### 2.1 告诉 Git 你是谁

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

### 2.2 配 SSH（推荐，一次配好不用输密码）

```bash
ssh-keygen -t ed25519 -C "你的邮箱"   # 一路回车
cat ~/.ssh/id_ed25519.pub              # 复制整行
```

粘到 GitHub → Settings → SSH and GPG keys → New SSH key。

```bash
ssh -T git@github.com                  # 看到 "Hi 用户名!" 就成功
```

### 2.3 建空仓库并初始化

GitHub 网页 → New repository → 名字 `arm-grasp` → **不要勾** Add README / .gitignore → Create。

```bash
mkdir -p ~/arm-grasp && cd ~/arm-grasp
cp <计划文件夹>/tools/git_helper.sh .
chmod +x git_helper.sh
./git_helper.sh init
./git_helper.sh remote git@github.com:你的用户名/arm-grasp.git
```

---

## 3. 每个命令到底做什么

| 命令 | 背后动作 | 什么时候用 | 注意 |
|---|---|---|---|
| `init` | 建目录骨架 + `.gitignore` + 首次提交 | 只在新建仓库时用一次 | 已是仓库会跳过 |
| `remote <URL>` | 设置 `origin` 并首次推送 | 第一次连 GitHub，或换远端地址 | 会改 `origin` 地址 |
| `save "说明"` | `git add -A && git commit` | 每跑通一个小功能 | **会提交所有改动**，先 `status` |
| `sync` | `git pull --rebase --autostash` + `git push` | 每天结束 / 每周日 | 有冲突会停，先解决再继续 |
| `tag <名字>` | 打标签并推送 | 里程碑，如 `w1-pass` | 标签名不要重复 |
| `undo` | `git reset --soft HEAD~1` | 刚提交错了，想重存 | **只在没 push 时用** |
| `back <文件>` | `git checkout -- 文件` | 丢弃某个文件的未提交改动 | **不可恢复**，会问你 y/N |
| `status` | `status -sb` + `diff --stat` | 每次 `save` 前 | `??` 是未跟踪文件 |
| `log` | 图形化最近 20 条 | 找回滚点 / 看历史 | 复制短 hash 用 |

---

## 4. 每天怎么用（30 秒）

```bash
cd ~/arm-grasp

# 1) 看状态
./git_helper.sh status

# 2) 存本地
./git_helper.sh save "feat(sim): IK 画圆跑通，误差 3.3mm"

# 3) 推云端（每天结束或每周日）
./git_helper.sh sync
```

如果 `save` 说“没有改动，无需提交”，说明你还没改文件，或者已经存过了，正常。

---

## 5. commit 说明怎么写

格式：`类型(范围): 做了什么/为什么`

```text
feat(sim): 跑通 KUKA IK 画圆
fix(serial): 修复半包解析导致的偶发丢帧
docs(hw): 补 ZED-M 首帧和深度有效率
test(transform): 加 3 个 pytest
wip(grasp): 下降能跑，夹爪还没接
```

类型：

- `feat` 新功能
- `fix` 修 bug
- `docs` 文档
- `test` 测试
- `refactor` 重构
- `exp` 实验
- `wip` 半成品
- `chore` 杂事

不要写：`update code`、`改了一下`、`111`。写“为什么”，以后自己看得懂。

---

## 6. 什么不要进仓库

| 类型 | 例子 | 怎么办 |
|---|---|---|
| 密钥/token | `.env`、密码 | 永不提交 |
| 大文件 | `.bag`、`.mp4`、`.npz`、模型权重 | `.gitignore` 已忽略，放 Release/网盘 |
| 日志/CSV | 抓取日志 | 只把结论写进 docs |
| 临时截图 | 桌面截图 | 放 `docs/media/` 前先想清楚 |

`save` 会 `git add -A`，所以**存之前先 `status`**，别把不该传的带上去。

---

## 7. 常见报错怎么办

| 报错 | 意思 | 怎么办 |
|---|---|---|
| `fatal: not a git repository` | 当前目录不是仓库 | `cd ~/arm-grasp` |
| `nothing to commit` | 没改动 | 正常 |
| `Please tell me who you are` | 没配用户名/邮箱 | 重做 §2.1 |
| `Permission denied (publickey)` | SSH 没配好 | 重做 §2.2 |
| `rejected ... (fetch first)` | 云端有你本地没有的提交 | 先 `./git_helper.sh sync` |
| `CONFLICT` | 同一文件两边都改了 | 打开文件，删 `<<<<<<<` 标记，保留要的，`git add 文件`，`git rebase --continue` |
| `detached HEAD` | 你不在任何分支上 | `git switch main` |
| `pathspec ... did not match` | 文件名打错 | `status` 看真实路径 |

看到 `fatal` 不要慌：它只表示“这一步没执行成功”，不代表代码坏了。

---

## 8. 三个救援场景

### ① 改坏了，想回滚

```bash
./git_helper.sh log
git switch -c rescue <短hash>
```

先在新分支回滚，不动 `main`。

### ② 刚提交错了，但还没 push

```bash
./git_helper.sh undo
./git_helper.sh save "fix: 重新提交"
```

`undo` 保留改动，只撤销 commit。

### ③ 已经 push 了，发现提交错了

不要 `git push --force`。再补一个 `fix:` 提交，历史保持完整；面试官看到“发现问题→修复”反而是加分项。

---

## 9. 一周节奏

| 频率 | 动作 |
|---|---|
| 每跑通一个小功能 | `save` |
| 每天结束 | 至少 1 次 `save` |
| 每周日 | `sync` + `tag w1` |
| 换阶段前 | `tag p0-pass` / `tag p1-pass` |

一周 3–10 个 commit 是正常节奏，不要攒到“做完再传”。

---

## 10. 你这个仓库的现状

```text
目录：~/arm-grasp
远端：git@github.com:ABlindArbiter/arm_grasp.git
分支：main
```

已经初始化过，不要再跑 `init`；日常只用：

```bash
./git_helper.sh status
./git_helper.sh save "说明"
./git_helper.sh sync
```
