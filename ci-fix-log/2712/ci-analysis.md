# CI 失败分析报告

## 基本信息
- PR: #2712 — Feat: add AI/xla/3b0ff80/24.03-lts-sp3
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Git短哈希无法作为远程ref
- 新模式症状关键词: `fatal: couldn't find remote ref`, `git fetch`, `--depth 1`, abbreviated SHA, `${VERSION}`

## 根因分析

### 直接错误
```
#10 [5/6] RUN git init . &&     git remote add origin https://github.com/openxla/xla.git &&     git fetch --depth 1 origin 3b0ff80 &&     git checkout FETCH_HEAD
#10 0.656 fatal: couldn't find remote ref 3b0ff80
#10 ERROR: process "/bin/sh -c git init . &&     git remote add origin https://github.com/openxla/xla.git &&     git fetch --depth 1 origin ${VERSION} &&     git checkout FETCH_HEAD" did not complete successfully: exit code: 128
```

### 根因定位
- 失败位置: `AI/xla/3b0ff80/24.03-lts-sp3/Dockerfile:21-24`
- 失败原因: Dockerfile 中 `git fetch --depth 1 origin ${VERSION}` 使用 7 字符的缩写 Git SHA（`3b0ff80`）作为远程 ref，Git 在 fetch 阶段无法解析缩写 SHA，报 `fatal: couldn't find remote ref`。

### 与 PR 变更的关联
PR 的变更直接触发了此失败。本次 PR 新增了 `AI/xla/` 镜像目录下的全部文件：
- `AI/image-list.yml` — 新增 `xla: xla` 条目
- `AI/xla/3b0ff80/24.03-lts-sp3/Dockerfile` — 新增 Dockerfile，第 23 行使用 `${VERSION}` 变量（值为 `3b0ff80`）作为 `git fetch` 的远程 ref 参数
- `AI/xla/README.md`、`AI/xla/doc/image-info.yml`、`AI/xla/doc/picture/logo.png`、`AI/xla/meta.yml` — 元数据及文档文件

错误发生在 Dockerfile 的步骤 `[5/6]`（git fetch 阶段），此前步骤 `[1/6]`（dnf install）和 `[3/6]`（bazelisk 下载）均成功，依赖安装和环境准备无误，问题完全出在 git 拉取源码的逻辑上。

## 修复方向

### 方向 1（置信度: 高）
Dockerfile 中 `ARG VERSION=3b0ff80` 使用了 7 字符的缩写 Git commit SHA，而 `git fetch origin ${VERSION}` 要求远程 ref 必须是完整 SHA（40 字符）、分支名或标签名。需要将 `VERSION` 值改为完整的 40 字符 SHA，或将 git 拉取逻辑从"fetch 特定 commit"改为"fetch 分支/tag 后 checkout 特定 commit"（如先 fetch 默认分支再 `git fetch origin <full-sha>`），或者在 fetch 时使用完整 SHA 并从 `FETCH_HEAD` checkout。

### 方向 2（置信度: 中）
若上游仓库 `openxla/xla` 中确实不存在 commit `3b0ff80`（或该 commit 已被 force-push 覆盖），则需要确认正确的目标 commit SHA 并更新 `VERSION` 变量。

## 需要进一步确认的点
1. 在 `https://github.com/openxla/xla` 仓库中确认 commit `3b0ff80` 的完整 40 字符 SHA 是否存在且可访问。
2. 确认该仓库是否有 tag 或 branch 指向该 commit，可替代 commit SHA 作为 fetch 目标。

## 修复验证要求
code-fixer 在提交前，必须从 `https://github.com/openxla/xla` 仓库获取 commit `3b0ff80` 的完整 40 字符 SHA，并验证使用完整 SHA 的 `git fetch --depth 1 origin <full-sha>` 在目标基础镜像（`openeuler/openeuler:24.03-lts-sp3`）中能够成功执行。
