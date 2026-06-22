# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码不匹配
- 新模式症状关键词: `error: Failed dependencies:`, `aarch64.rpm`, `rpm -ivh`, `foundationdb-clients`, `x86_64-unknown-linux-gnu`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
------
Dockerfile:22
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`（第5/9步 RUN 指令）
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构，但当前 CI 构建环境运行的是 x86_64 架构（日志中 rust 安装器输出 `default host triple is x86_64-unknown-linux-gnu`，fuse 构建输出 `Host machine cpu: x86_64` 均可证实）。aarch64 架构的 RPM 包在 x86_64 容器中无法安装，其声明的依赖 `libm.so.6(GLIBC_2.17)` 在 openEuler 基础镜像中也无法通过 `rpm -ivh`（不自动解析依赖）满足。

### 与 PR 变更的关联
本次 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（全新文件，69 行），其中的 FoundationDB RPM 安装步骤（第 22-24 行）直接导致了 CI 失败。该步骤存在两个问题：

1. **架构硬编码**：URL 固定使用 `aarch64`，未根据构建目标架构动态选择 `x86_64` 或 `aarch64` RPM。
2. **依赖解析缺失**：使用 `rpm -ivh`（不解析依赖）安装 EL9 体系 RPM，而 openEuler 的 glibc 包名/版本可能与 EL9 不同，需改用 `yum localinstall` 或添加 `--nodeps`。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 的下载架构从硬编码改为动态选择。可使用 `$(uname -m)` 或 BuildKit 内置 ARG `TARGETARCH` 来构造正确的 RPM 文件名（FoundationDB 在 GitHub Releases 同时提供 `el9.x86_64.rpm` 和 `el9.aarch64.rpm`）。

### 方向 2（置信度: 中）
将 `rpm -ivh` 替换为 `yum localinstall -y`，以便自动解析并安装 FoundationDB RPM 所需依赖（如 glibc 对应版本），避免 `Failed dependencies` 错误。若 openEuler yum 源中的 glibc 版本与 FoundationDB RPM 的 EL9 依赖不兼容，可考虑用 `rpm -ivh --nodeps` 绕过依赖检查。

### 方向 3（置信度: 低，参考历史模式）
修复当前 FoundationDB 安装问题后，Dockerfile 中后续的 `git clone --depth 1` + commit hash checkout 步骤（第 29-30 行）可能触发**模式18**（浅克隆无法检出历史 commit hash），CI 可能继续失败。code-fixer 应一并检查并修复该步骤。

## 需要进一步确认的点
1. 需确认 FoundationDB 7.3.77 的官方 GitHub Release 中 `el9.x86_64` RPM 是否确实存在（URL: `https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.x86_64.rpm`）。
2. 需确认 openEuler 24.03-LTS-SP3 基础镜像中 glibc 版本是否满足 FoundationDB RPM 的 `GLIBC_2.17` 符号版本要求。若不满足，需改用 `--nodeps` 安装并验证 FoundationDB 客户端实际运行是否正常。
3. 历史知识库中模式18提及本 PR 存在 `git clone --depth 1` + commit hash checkout 不兼容的**潜在后续问题**，code-fixer 应在修复 FoundationDB 安装后验证整个 Docker build 能否完整通过。
