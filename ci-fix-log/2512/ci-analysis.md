# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: lint-error
- 置信度: 高
- 知识库匹配: 模式11
- 其他关联模式: 模式18（潜在问题，本次 CI 未触发）

## 根因分析

### 直接错误
```
2026-06-04 17:22:14,799-.../update.py[line:273]-ERROR: There are some specification errors for releasing on appstore in this PR, please check as above.
+--------------------------+------------------------------------------------------------+--------------+
|       Check Items        |                        Description                         | Check Result |
+--------------------------+------------------------------------------------------------+--------------+
| .claude/agents/README.md | [Path Error] The expected path should be .claude/README.md |   FAILURE    |
+--------------------------+------------------------------------------------------------+--------------+
Build step 'Execute shell' marked build as failure
Finished: FAILURE
```

### 根因定位
- 失败位置: `.claude/agents/README.md`（期望位置 `.claude/README.md`）
- 失败原因: CI appstore 发布规范预检要求 `.claude/` 工具目录的 README 文件位于 `.claude/README.md`（根层级），但 PR 将其放在了 `.claude/agents/README.md`（子目录 agents 内）。

### 与 PR 变更的关联
PR 进行了大规模重命名：将工具目录从 `.agents/` 迁移到 `.claude/`。在此过程中，`README.md` 原本位于 `.agents/agents/README.md`，被重命名为 `.claude/agents/README.md`。但 CI 预检规则期望 `.claude/` 目录的 README 位于 `.claude/README.md`，而非 `.claude/agents/README.md`。该预检在 Dockerfile 构建启动前即失败，导致构建流程被阻断。

另外，PR diff 中引入了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 新文件（52 行），其中第 22-24 行使用了 `git clone --depth 1` + `git checkout ${VERSION}` 模式，对应历史模式18（git 浅克隆与 commit hash checkout 不兼容）。但由于 CI 在预检阶段即失败，Dockerfile 构建从未执行，该问题**尚未暴露**在当前日志中。

## 修复方向

### 方向 1（置信度: 高）
将 `.claude/agents/README.md` 移动到 `.claude/README.md`，即从 `agents` 子目录提升到 `.claude/` 根层级，同时更新文件中 `python3 .claude/run_workflow.py` 和 `python3 .claude/scripts/setup_symlinks.py` 的相对路径引用以适应新位置（当前引用是相对于仓库根的，移到根层级后应仍然正确，但需验证）。

### 方向 2（置信度: 中）
修复 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24` 的 git 浅克隆兼容性问题：将 `git clone --depth 1` 改为完整克隆或增加 `git fetch origin ${VERSION}` 后再 checkout，确保指定 commit hash 能被正确拉取。此问题虽非当前失败的直接原因，但通过预检后构建阶段极可能触发失败（参见模式18）。

## 需要进一步确认的点
1. 确认 CI appstore 预检规则的完整 schema：`.claude/` 目录下的 `README.md` 是否强制要求在根层级，以及 `.claude/agents/` 内的其他文件（如各 agent 的 `.md` 文件）是否有路径规范要求。
2. 确认 Dockerfile 第 22-24 行 `git clone --depth 1` + commit hash checkout 的组合在实际构建中是否确实会失败（需等预检通过后 x86-64/aarch64 构建 job 日志验证）。模式18 中已有同类案例记录，修复可提前进行。
