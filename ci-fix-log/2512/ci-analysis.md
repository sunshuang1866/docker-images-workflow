# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM跨发行版依赖不满足
- 新模式症状关键词: error: Failed dependencies, libm.so.6(GLIBC_2.17), foundationdb-clients, el9, openEuler

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: FoundationDB 官方仅发布 RHEL/CentOS 7/9 (el7/el9) 的 RPM 包，其 RPM 自动依赖声明 `libm.so.6(GLIBC_2.17)(64bit)` 与 openEuler 24.03 的 glibc RPM provides 不兼容，导致 `rpm -ivh` 依赖解析失败。

附加观察：构建日志中 meson 输出 `Host machine cpu family: x86_64`、rustup 输出 `default host triple is x86_64-unknown-linux-gnu`，确认本次 CI 在 x86_64 平台上构建。但 Dockerfile 中 FoundationDB RPM URL 硬编码了 `aarch64` 架构后缀——即使依赖问题解决，该 URL 也会导致架构不匹配（x86_64 构建应使用 `x86_64` 的 RPM）。

### 与 PR 变更的关联
PR #2512 新增了完整的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行），FoundationDB RPM 安装步骤（第 22-24 行）是此新增 Dockerfile 的一部分。该失败由 PR 直接引入。

## 修复方向

### 方向 1（置信度: 高）
FoundationDB 官方不提供 openEuler 原生 RPM，需放弃 `rpm -ivh` 方式，改为从 FoundationDB 官方 tar 包中提取 `fdbcli` 等客户端二进制文件。FoundationDB 在 GitHub Releases 同时发布 `.tar.gz` 格式的客户端包，解压后直接复制所需二进制到镜像中，绕过 RPM 依赖检查。

### 方向 2（置信度: 中）
如必须在 openEuler 上安装 FoundationDB 客户端，可尝试用 `rpm -ivh --nodeps` 跳过依赖检查强制安装，然后手动验证 `fdbcli` 二进制能否正常运行。此方法有运行时兼容性风险——el9 RPM 链接的 glibc 符号可能与 openEuler 不完全兼容。

### 方向 3（置信度: 中）
修复架构硬编码问题：Dockerfile 需根据构建架构动态选择 `x86_64` 或 `aarch64` 的 RPM URL，而非硬编码 `aarch64`。使用 BuildKit 预定义 `TARGETARCH` ARG 或 shell 变量 `$(uname -m)` 构造正确的下载 URL。

## 需要进一步确认的点
1. 需确认 FoundationDB 7.3.77 在 GitHub Releases 是否同时提供 `x86_64` 和 `aarch64` 的 `.tar.gz` 客户端包（`foundationdb-clients-7.3.77-1.el9.x86_64.tar.gz` 及对应 aarch64 版本），以及解压后的目录结构和二进制文件列表。
2. 需确认 `fdbcli` 在 openEuler 24.03 上的运行时库依赖（`ldd fdbcli`）是否全部可满足；若缺少特定 `.so` 版本，需在 `yum install` 步骤中补充对应运行时包。
3. Dockerfile 中还存在历史模式已识别的其他潜在问题（`boost-foundation` 包名不存在、`--depth 1` 浅克隆与 commit hash checkout 不兼容、`2>/dev/null || true` 掩盖错误），这些在 FoundationDB 步骤失败后被跳过执行，需一并修复。

## 修复验证要求
code-fixer 在提交修复前必须：
1. 从 https://github.com/apple/foundationdb/releases/tag/7.3.77 确认 `foundationdb-clients-7.3.77-1.el9.x86_64.tar.gz` 和 `foundationdb-clients-7.3.77-1.el9.aarch64.tar.gz` 的实际存在性与内部文件布局。
2. 在 openEuler 24.03 容器中验证所选安装方式（tar 解压或 `--nodeps`）后的 `fdbcli --version` 能正常执行。
3. 若采用 tar 方式，需在 Dockerfile 中根据 `TARGETARCH`（或 `$(uname -m)` 结果 `x86_64`/`aarch64`）动态选择正确的下载 URL，确保两架构构建均能通过。
