# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式18
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
（注：CI 日志仅包含 trigger job 输出，其本身 `Finished: SUCCESS`。下游 x86-64 (#1357) 和 aarch64 (#1332) 构建 job 的实际日志未提供，两者均报告 `FAILURE`。）

下游构建 job 的实际错误日志缺失，但基于 PR diff 和知识库记录可精确定位根因。

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: `git clone --depth 1` 浅克隆后，`git checkout ${VERSION}` 尝试检出 commit hash `22fca04`，但该 commit 不在浅克隆可访问范围内；同时 `2>/dev/null || true` 静默掩盖了 checkout 失败，导致构建在错误源码上执行。

Dockerfile 中关键片段（第 20-24 行）：
```dockerfile
git clone --recurse-submodules --depth 1 --shallow-submodules https://github.com/deepseek-ai/3fs /tmp/3fs && \
git -C /tmp/3fs checkout ${VERSION} 2>/dev/null || true && \
git -C /tmp/3fs submodule update --init --recursive --depth 1 2>/dev/null || true && \
```

其中 `ARG VERSION=22fca04` 是一个 7 字符 commit hash（非 tag/分支名），`--depth 1` 只拉取默认分支最新提交，commit `22fca04` 历史不在其中，checkout 静默失败。后续 `./patches/apply.sh`、`cmake`、`cmake --build` 均在错误的源码版本上执行，导致编译失败。

### 与 PR 变更的关联
本次 PR 新增的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 是全新文件，上述 `git clone --depth 1` + commit hash checkout 的 anti-pattern 由该 PR 直接引入。此外，三处 `2>/dev/null || true` 均掩盖了潜在错误（checkout 失败、submodule 更新失败、systemd service 文件复制失败）。

**次要问题**：新增的 5 个文件（Dockerfile、README.md、meta.yml、image-info.yml、image-list.yml 条目不适用）均缺少 Copyright/SPDX-License-Identifier 头，CI 已产生 `WARNING: 缺少项目级Copyright声明文件` 告警（知识库 模式17），此告警当前未阻塞构建但可能导致后续合规检查失败。

## 修复方向

### 方向 1（置信度: 高）— 修复 git clone 与 commit hash checkout 不兼容
去掉 `--depth 1` 改为完整克隆，或保留 `--depth 1` 但在 checkout 前增加 `git fetch origin ${VERSION}`。同时去除 checkout 和 submodule update 上的 `2>/dev/null || true` 掩错逻辑，让错误显式暴露。

### 方向 2（置信度: 中）— 补充 Copyright/SPDX 头
为所有新增文件（`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`、`Storage/3fs/README.md`、`Storage/3fs/meta.yml`、`Storage/3fs/doc/image-info.yml`）添加 Copyright 和 SPDX 声明头（MulanPSL-2.0），格式参照模式17。

## 需要进一步确认的点
1. 下游 x86-64 (#1357) 和 aarch64 (#1332) 构建 job 的实际错误日志未提供，无法确认除 git checkout 外是否还有其他编译/依赖错误（如 fuse3 源码构建冲突、3FS 特定 cmake 参数 `-DSHUFFLE_METHOD=g++11` 版本兼容性、patches/apply.sh 补丁应用失败等）。建议获取完整构建日志后做二次分析。
2. `VERSION=22fca04` 是否为 deepseek-ai/3fs 仓库中实际存在的 commit，需确认其与最近一次提交的对应关系 — 若该 commit 已被 GC 或不在默认分支历史中，即使修复克隆深度也无法 checkout。
