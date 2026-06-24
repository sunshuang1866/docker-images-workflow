# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM跨发行版架构不匹配
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6(GLIBC`, `rpm -ivh`, `el9`, `aarch64`, `x86_64`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && rpm -ivh /tmp/fdb-clients.rpm && rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
------

Dockerfile:22
--------------------
  21 |     
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
  25 |     
--------------------
ERROR: failed to solve: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`
- 失败原因: Dockerfile 硬编码下载 `el9.aarch64` 架构的 FoundationDB RPM，但此 CI 构建作业运行在 x86_64 平台上（meson 输出确认 `Host machine cpu: x86_64`），且 RPM 的 glibc 依赖声明（`GLIBC_2.17`）与 openEuler 的软件包数据库不兼容，导致 `rpm -ivh` 依赖解析失败

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（新增 69 行），该 Dockerfile 的第 22-24 行即为失败的 FoundationDB RPM 安装步骤。此失败直接由本次 PR 引入的新代码触发。

**注意**：当前日志只展示了 x86_64 架构的 CI 构建作业。若 aarch64 架构的构建作业另有日志，可能会出现不同的错误（如 glibc 版本符号实际可用但仍因 rpm 依赖声明格式不兼容而失败，或更深层的构建依赖缺失）。本次报告基于提供的 x86_64 日志进行分析。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的架构部分改为动态获取（使用 BuildKit 内置 ARG `TARGETARCH` 或 shell 命令 `uname -m`），使 x86_64 构建下载 `x86_64` 架构 RPM、aarch64 构建下载 `aarch64` 架构 RPM。同时需验证 FoundationDB 官方是否提供 `x86_64` 架构的 RPM（URL 中的 `aarch64` 需替换为 `x86_64` 或 `amd64`）。

### 方向 2（置信度: 中）
FoundationDB `el9` RPM 的依赖声明格式可能与 openEuler 的 RPM 数据库不兼容（即使在正确架构上）。可考虑改为从 FoundationDB 官方 Docker 镜像中 `COPY` 二进制文件（多阶段构建），或从 FoundationDB 源码编译安装，完全绕过跨发行版 RPM 兼容性问题。

## 需要进一步确认的点

1. **FoundationDB 官方是否提供 x86_64/amd64 架构的 RPM**：需检查 `https://github.com/apple/foundationdb/releases/download/7.3.77/` 下是否存在 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 或类似命名的 x86_64 包。
2. **即使架构修复后，`el9` RPM 在 openEuler 上是否可用**：需在 openEuler 24.03 容器中实际测试 `rpm -ivh` 安装 FoundationDB `el9` RPM，确认无其他隐藏的依赖冲突（当前日志仅暴露了第一个依赖失败，修复后可能暴露更多）。
3. **此 Dockerfile 存在知识库已记录的其他潜在问题**：
   - 模式18（`--depth 1` + commit hash checkout 不兼容）：Dockerfile 中 `git clone --recurse-submodules --depth 1` 后 `git checkout ${VERSION}` 可能因浅克隆无法访问历史 commit 而失败，且 `2>/dev/null || true` 静默掩盖了错误。RPM 步骤修复后，此问题可能成为下一个阻塞点。
   - 模式10（缺构建依赖/包名错误）：知识库提及 `boost-foundation` 包名问题，需验证 openEuler yum repo 中是否存在该包名。
4. **aarch64 架构构建作业的日志**：当前仅提供 x86_64 日志，需获取 aarch64 构建作业日志以确认是否存在其他架构专属问题。

## 修复验证要求

### RPM URL 架构动态化验证
若修复方向选择动态化 RPM 下载 URL：
1. code-fixer 必须在 openEuler 24.03 容器中验证 FoundationDB 官方 GitHub Release 页面确实存在目标架构的 RPM 文件（检查 `https://github.com/apple/foundationdb/releases/tag/7.3.77` 的发布资产列表）。
2. code-fixer 必须分别用 x86_64 和 aarch64 架构的 openEuler 容器测试 `rpm -ivh` 安装对应的 FoundationDB RPM，确认无依赖冲突。

### 浅克隆修复验证
若修复方向涉及 git clone 步骤：
1. code-fixer 必须确认 commit `22fca04` 在 `deepseek-ai/3fs` 仓库的 `--depth 1` 浅克隆中是否可访问（不可访问时需改为 `git fetch origin ${VERSION}` 方式）。
