# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码错误
- 新模式症状关键词: `error: Failed dependencies`, `rpm -ivh`, `aarch64`, `x86_64`, `hardcoded architecture`, `foundationdb`

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
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码了 `aarch64` 架构，而 CI 构建在 x86_64 架构上运行，导致 RPM 依赖解析失败（aarch64 包在 x86_64 系统上无法解析其架构特定的库依赖）。

证据：
- 构建日志显示 `default host triple is x86_64-unknown-linux-gnu`（步骤 #8）
- 构建日志显示 `Host machine cpu family: x86_64`（步骤 #9 fuse 编译）
- Dockerfile 第 22 行 URL 固定为 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`

### 与 PR 变更的关联
此 Dockerfile 由 PR #2512 全新引入（`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 为新增文件），其中的 FoundationDB RPM 安装步骤硬编码了 aarch64 架构，未考虑多架构构建场景。该错误由本次 PR 变更直接引入。

## 修复方向

### 方向 1（置信度: 高）
将 foundationdb RPM 下载 URL 中的架构部分从硬编码 `aarch64` 改为动态检测当前构建架构。使用 `uname -m` 或 BuildKit 的 `TARGETARCH` 变量，将 aarch64 映射为 `aarch64`、x86_64 映射为 `x86_64`，构造正确的 RPM 文件名。需注意 FoundationDB 对 openEuler 的兼容性——el9 包的依赖（如 glibc 版本符号）在 openEuler 上可能不完全匹配，如果修正架构后仍有依赖错误，需考虑从源码编译 fdb clients 或改用 FoundationDB 官方提供的通用 Linux 二进制包。

### 方向 2（置信度: 中）
如果 FoundationDB 不提供适用于 openEuler 的 RPM 包（x86_64 版本同样存在 glibc 版本符号不匹配），改用 FoundationDB 官方 Docker 镜像进行多阶段构建，从其镜像中 `COPY` 客户端二进制文件。类似模式16（RPM 包停止发布时用多阶段构建绕过）。

### 潜在后续问题（修正 RPM 架构后可能暴露）
1. **Pattern 18 — git 浅克隆与 commit hash checkout 不兼容**：Dockerfile 中 `git clone --depth 1` 后 `git checkout ${VERSION} 2>/dev/null || true`，浅克隆无法 checkout 历史 commit hash（`22fca04`），`|| true` 静默掩盖错误，导致构建使用了错误的源码版本。
2. **Pattern 10 — 运行时包名不存在**：最后一层 `yum install` 中 `boost-foundation` 在 openEuler 仓库中不存在（知识库 pattern 10 已有记录）。

## 需要进一步确认的点
1. FoundationDB 7.3.77 是否提供 `x86_64` 架构的 el9 RPM 包（URL: `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`）
2. el9 的 RPM 包在 openEuler 24.03-LTS-SP3 上是否存在 glibc 版本符号兼容性问题（`GLIBC_2.17` 虽老，但 RPM provides 校验机制可能因发行版差异而失败）
3. 如需改用多阶段构建，FoundationDB 官方 Docker 镜像中客户端二进制路径（`/usr/bin/fdbcli` 等）需确认
