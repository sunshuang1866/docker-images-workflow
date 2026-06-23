# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构/发行版不匹配
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6`, `GLIBC_`, `rpm -ivh`, `aarch64`, `el9`, `foundationdb`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中硬编码了 `aarch64` 架构的 FoundationDB RPM URL（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），但 CI 构建环境为 x86_64（日志 `#8: default host triple is x86_64-unknown-linux-gnu` 证实），跨架构 RPM 导致依赖解析失败——rpm 无法在 x86_64 系统上为 aarch64 包解析 `libm.so.6(GLIBC_2.17)(64bit)` 依赖。

### 与 PR 变更的关联
本次失败**完全由 PR 新增的 3FS Dockerfile 引起**。该 Dockerfile（`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`）是 PR 新增文件（`new_file: True, added_lines: 69`），其中 FoundationDB 安装步骤（第 22-24 行）将 RPM 下载 URL 硬编码为 `aarch64` 架构，未使用 BuildKit 的 `TARGETARCH` 或类似机制按运行时架构动态选择正确的 RPM 包。此问题与此前目录重组（`.agents/` → `.claude/`）无关。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的 `aarch64` 替换为架构变量（如 BuildKit 的 `TARGETARCH` 或 shell 中 `uname -m` 推导），使 x86_64 构建下载 `x86_64` RPM、aarch64 构建下载 `aarch64` RPM。注意 FoundationDB 的架构命名：x86_64 平台在 Apple 发布页使用 `x86_64`（非 `amd64`），ARM 使用 `aarch64`（非 `arm64`），需做映射。同时需确认 FoundationDB `7.3.77` 版本在 ARM (`aarch64`) 平台也发布了 RPM 制品。

### 方向 2（置信度: 中）
即使架构匹配，FoundationDB 的 `.el9` RPM 是为 RHEL/CentOS 9 构建的，在 openEuler 24.03 上可能存在运行时库版本差异。若架构修复后仍出现 glibc 或其他依赖不兼容，需考虑改用 FoundationDB 官方多架构 Docker 镜像的多阶段构建方案，从 `foundationdb/foundationdb:7.3.77` 中 `COPY --from` 提取客户端库文件。

## 需要进一步确认的点

1. **FoundationDB 7.3.77 是否发布了 x86_64 RPM**：需确认 `https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 是否存在（HTTP 200）。
2. **FoundationDB 7.3.77 在 aarch64 平台的 RPM 是否可用**：历史日志中 aarch64 RPM 下载成功（curl 未报 404），但 `rpm -ivh` 失败是因为跨架构。需单独验证 aarch64 构建环境下该 RPM 能否正常安装。
3. **修复 FoundationDB 后需关注的下一个潜在失败（模式18）**：Dockerfile 中 `git clone --recurse-submodules --depth 1` 结合 `git checkout ${VERSION}`（VERSION=22fca04，是一个 commit hash 的前 7 位）存在浅克隆不兼容问题——`--depth 1` 只包含最新提交，指定 commit hash 可能不可达。历史模式18 已记录此问题。修复 FoundationDB 安装后，下一个构建步骤可能暴露此错误。
4. **`.el9` RPM 在 openEuler 上的兼容性**：即使架构正确，`.el9` RPM 对 `libm.so.6(GLIBC_2.17)` 的依赖在 openEuler 24.03（glibc 版本不同）上是否能被满足，目前日志证据不足。
