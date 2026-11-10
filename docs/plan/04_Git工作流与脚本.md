# Git 工作流（给「只在最后传一次」的人）

> 你现在的模式：本地开发三个月 → 全部完成后 `git init` + 传一次。
> 先解释一下：下面所有英文都是 Git 自带的术语，没有一个是必须背的。**先看 §0 的对照表，你会发现它其实就是"存档"这一件事的不同侧面。**

---

## 0. 先看这个：Git 术语人话对照

> 看完这张表，90% 的英文你都能猜出来了。

| 英文 | 中文 | 人话（类比游戏） |
|---|---|---|
| repository / repo | 仓库 | 你的项目文件夹 + 里面所有存档历史 |
| commit | 提交 | **存一次档**。一次 commit = 一个存档点 |
| stage / index | 暂存区 | 购物车：你挑好哪些改动要放进这次存档 |
| branch | 分支 | 平行世界。`main` 是正式世界，`exp/xxx` 是实验世界 |
| main / master | 主分支 | 正式世界。别人（和面试官）默认打开的就是它 |
| HEAD | 头指针 | 你现在站在哪个存档点上 |
| remote | 远端 | 云端的那个仓库（GitHub 上的） |
| origin | 远端别名 | 给云端仓库起的默认小名，叫 `origin` |
| upstream | 上游 | 你本地分支跟踪的那个云端分支 |
| push | 推送 | 把本地存档**传到**云端 |
| pull | 拉取 | 把云端存档**拿下来并合并**进来 |
| fetch | 获取 | 只拿下来看看，先不合并 |
| clone | 克隆 | 把整个仓库（含历史）复制到本地 |
| merge | 合并 | 把一个平行世界并进当前世界 |
| rebase | 变基 | 把你的改动"挪到"别人改动之后。会改写历史，**慎用** |
| conflict | 冲突 | Git 不知道留哪个版本，让你人来选 |
| tag | 标签 | 给某个存档贴个名字，比如 `w1-pass`、`v1.0` |
| diff | 差异 | 改了什么（新增/删除的行） |
| checkout / switch | 切换 | 跳到另一个存档 / 另一个分支 |
| reset | 重置 | 撤销提交（分软/硬，硬的会删改动） |
| stash | 暂存（藏起来） | 改动先藏一边，工作区变干净 |
| .gitignore | 忽略清单 | 写在这儿的文件，Git 永远不管 |
| working tree clean | 工作区干净 | 没有未存档的改动 |
| detached HEAD | 游离头指针 | 你不在任何分支上（切到某个旧存档了） |

**一句话总结**：Git 就是「**存档 + 平行世界 + 云端备份**」。所有英文都在描述这三件事。

---

## 1. 为什么值得改：三个具体损失

1. **丢代码**：硬盘、系统重装、误删，任何一次都归零。调参记录只存在脑子里，尤其危险。
2. **不能回滚**：硬件调试最常见的场景是「昨天还能跑，今天改了三处，动不了了」。没有存档点，你只能凭记忆往回改。
3. **招聘方看到的是「压缩包」**：一个仓库只有 1 个 commit，别人无法判断哪些是你写的、做了多久。**commit 历史是「亲手做过」最直接的证据**。

---

## 2. 心智模型：commit 是存档点，不是发布

- **commit ≠ 上传**。commit 完全在本地，不需要网络，不需要别人看，可以很丑。
- **push 才是备份/展示**。每周一次就够。
- 允许「半成品 commit」，信息写清楚做到哪了，比如 `wip(ik): 肘上解能算，肘下还没处理`。
- 判断标准只有一个：**如果现在电脑坏了，这个 commit 能不能让我少难受一点？**

游戏存档没人要求「通关才能存」，代码也一样。

---

## 3. 三层节奏

| 频率 | 动作 | 耗时 | 目的 |
|---|---|---|---|
| 每跑通一个小功能 | `save "说明"` | 10 秒 | 存档点 |
| 每天结束 | 至少 1 次 `save` | 10 秒 | 当天成果落地 |
| 每周日 | `sync` + `tag w10` | 1 分钟 | 备份到云端 + 里程碑 |

一周 3–10 个 commit 是正常节奏。

---

## 4. 第一次配置（Ubuntu，10 分钟）

### 4.1 告诉 git 你是谁

```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

### 4.2 配 SSH（推荐，一次配好以后不用输密码）

```bash
ssh-keygen -t ed25519 -C "你的邮箱"        # 一路回车
cat ~/.ssh/id_ed25519.pub                   # 复制输出的整行
```

把复制的内容粘到 GitHub → Settings → SSH and GPG keys → New SSH key。

```bash
ssh -T git@github.com     # 看到 "Hi 用户名!" 就成功
```

> 不想配 SSH 就用 HTTPS，第一次 push 会让你输入 token（GitHub 密码不能用于 git，要去 Settings → Developer settings → Personal access tokens 生成，勾 `repo`）。

### 4.3 建空仓库 + 本地初始化

GitHub 网页 → New repository → 名字 `arm-grasp` → **不要勾** Add README / .gitignore → Create。

```bash
mkdir -p ~/arm-grasp && cd ~/arm-grasp
cp /path/to/tools/git_helper.sh .
chmod +x git_helper.sh
./git_helper.sh init
```

### 4.4 连上远端并首次推送

```bash
./git_helper.sh remote git@github.com:你的用户名/arm-grasp.git
```

---

## 5. 日常只用五个命令

脚本的输出全是中文，你不需要记 git 参数：

| 你想干什么 | 命令 | 背后其实做了 |
|---|---|---|
| 存个档 | `./git_helper.sh save "改了什么"` | `git add -A && git commit` |
| 备份到云端 | `./git_helper.sh sync` | `git pull --rebase && git push` |
| 打个里程碑 | `./git_helper.sh tag p2-pass` | 打 tag 并推送 |
| 撤销上一次提交（保留改动） | `./git_helper.sh undo` | `git reset --soft HEAD~1` |
| 看看现在什么状态 | `./git_helper.sh status` | `status -sb` + `diff --stat` |

加个别名少打字：

```bash
echo "alias ag='./git_helper.sh'" >> ~/.bashrc && source ~/.bashrc
ag save "ik 解析解跑通"
```

---

## 6. 提交信息怎么写（30 秒学会）

格式：`类型(范围): 做了什么`

```
feat(ik): 解析解支持肘上/肘下两解
fix(serial): 修复半包解析导致的偶发丢帧
docs(dh): 补 J5 自转零位测量结果
exp(servo): 试了 3 种加速度曲线，梯形最稳
wip(grasp): 流水线跑到下降，夹爪还没接
```

类型：`feat` 新功能 · `fix` 修 bug · `docs` 文档 · `test` 测试 · `refactor` 重构 · `exp` 实验 · `wip` 半成品 · `chore` 杂事。

**关键不是格式，是「为什么」。**

- ❌ `update code`
- ✅ `fix(serial): 半包导致偶发丢帧，改为按帧头重同步`

---

## 7. 分支：只用两条

```
main      永远保持「能跑」。面试官点进来看到的就是它。
exp/xxx   实验分支。改坏了直接删，不影响 main。
```

```bash
git switch -c exp/new-ik      # 开实验分支
git switch main               # 回正式世界
git merge exp/new-ik          # 实验成功，合并
git branch -D exp/new-ik      # 实验失败，删掉
```

**硬件调试专用规则**：每次改 DH 参数、限位、标定矩阵之前，先 `git tag baseline-<日期>`。改坏了 `git switch -c fix/xx baseline-...` 就能回到已知能跑的状态。

---

## 8. `init` 会建出来的结构

```
arm-grasp/
├── README.md
├── .gitignore
├── docs/{hardware,dh_table,calibration,debug_log}.md
├── docs/media/.gitkeep
├── firmware/stm32/.gitkeep
├── pc/{arm,vision,grasp,ros2_bridge,config,tests}/.gitkeep
├── sim/urdf/.gitkeep
├── tools/git_helper.sh
└── scripts/.gitkeep
```

`.gitignore` 已覆盖 Python / C 编译产物 / ROS2 的 `build install log` / bag / 模型权重 / 日志 / 图片视频（`docs/media/` 除外）。

---

## 9. 什么不要进仓库

| 类型 | 例子 | 怎么办 |
|---|---|---|
| 视频 | demo.mp4 | 传 B 站，README 放链接 |
| 数据集 / bag | `*.bag`、`*.db3` | 不进 git，放 Release |
| 模型权重 | `*.pt`、`*.onnx` | 放 Release，代码里写下载脚本 |
| 日志 / CSV | 抓取日志 | 不进 git，只把结论表写进 docs |
| 密钥 / token | `.env` | 永不提交 |

> 判断标准：**这个文件能不能用一段文字/一张图代替？** 能，就别进 git。

---

## 10. 常见英文报错对照（看到别慌）

Git 的报错通常只有第一行有用，后面是文件列表。对照着看：

| 报错（英文） | 中文意思 | 怎么办 |
|---|---|---|
| `fatal: not a git repository` | 当前目录不是仓库 | `cd` 到项目根目录，或 `./git_helper.sh init` |
| `nothing to commit, working tree clean` | 没有改动可存 | 正常，不用管 |
| `Please tell me who you are` | 没配用户名邮箱 | 跑一遍 §4.1 |
| `fatal: remote origin already exists` | 远端已经配过了 | `git remote set-url origin <新地址>`（脚本 `remote` 会自动处理） |
| `Permission denied (publickey)` | SSH 没配好 | 重做 §4.2，或改用 HTTPS + token |
| `rejected ... (fetch first)` / `failed to push some refs` | 云端有你本地没有的提交 | 先 `./git_helper.sh sync` |
| `CONFLICT (content): Merge conflict in 文件` | 冲突，同一个文件两边都改了 | 打开文件，删掉 `<<<<<<<` `=======` `>>>>>>>` 标记，保留要的版本，然后 `git add 文件 && git commit` |
| `You are in 'detached HEAD' state` | 你不在任何分支上 | `git switch main` |
| `Your branch is ahead of 'origin/main' by N commits` | 本地比云端多 N 个提交 | `./git_helper.sh sync` |
| `Changes not staged for commit` | 改了但没放进购物车 | `./git_helper.sh save "说明"` |
| `error: pathspec 'xxx' did not match` | 文件名打错了 | 用 `git status` 看真实路径 |

> 记住一件事：**报错里带 `fatal` 不代表代码坏了，只代表这一步命令没执行成功。** 先看第一行，别被一屏英文吓到。

---

## 11. 三个翻车场景的救援

**① 改坏了，想回到昨天能跑的版本**

```bash
./git_helper.sh log                 # 找 commit 短 hash
git switch -c rescue <hash>         # 在新分支回到那个版本（不动 main）
```

只恢复某个文件：`git checkout <hash> -- pc/arm/ik.py`

**② 刚 commit 了，发现漏文件 / 信息写错**

```bash
./git_helper.sh undo
./git_helper.sh save "正确信息"
```

**③ 已经 push 了不该提交的大文件**

```bash
git rm --cached 大文件
echo "大文件路径" >> .gitignore
git commit -m "chore: 移除误提交的大文件"
```

历史里还有，但以后不会更大。**不要**为这个去学 `filter-branch`。

---

## 12. 每周日 15 分钟例行

- [ ] `status` 看有没有忘存的
- [ ] `save "本周小结"`（如果还有改动）
- [ ] `sync`
- [ ] 有验收通过 → `tag w10-pass`
- [ ] 更新 `01_进度台账.md`，一并提交
- [ ] 看一眼 `log`：这周有 3 个以上 commit 吗？

---

## 13. 招聘方会看什么

- **commit 节奏**：每周都有 = 持续在做；三个月一个 = 像压缩包。
- **提交信息**：能看出你是否理解自己改的东西。
- **tag / 分支**：有没有版本概念。
- **README**：第一眼。
- **不要 force push 到 main**：会覆盖历史，是协作红线。

你在 §7 调试专项里练的「留证据」，和这里的「留 commit」是同一件事：**让工作可复现、可追溯**。面试时说「我每次改标定参数前都会打 baseline tag」，比说「我很细心」有说服力。

---

## 附：如果你只有 5 分钟

1. `save` 随时用，一天至少一次。
2. 大改之前 `tag baseline-日期`。
3. 每周日 `sync`。
4. 英文报错只看第一行，对照 §10。
