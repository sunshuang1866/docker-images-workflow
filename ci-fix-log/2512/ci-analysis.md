# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码
- 新模式症状关键词: error: Failed dependencies, rpm -ivh, aarch64, GLIBC_2.17, libm.so.6

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
- 失败原因: FoundationDB RPM 下载 URL 硬编码为 `aarch64` 架构，但 CI 构建环境实际运行在 **x86_64** 平台（日志证据：Rust 编译目标 `x86_64-unknown-linux-gnu`、fuse meson 检测 `Host machine cpu: x86_64`）。RPM 架构与宿主机不匹配导致依赖解析失败。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（+69 行），该文件第 22-24 行的 FoundationDB 安装步骤硬编码了 aarch64 RPM URL，无架构自适应逻辑。这是本次 PR 直接引入的错误。

此外，该 Dockerfile 存在一个已被知识库记录的**潜伏问题**（模式18）：`git clone --depth 1` 浅克隆后通过 `|| true` 静默忽略 `git checkout ${VERSION}` 的失败，即使用 commit hash 作为版本号 `22fca04` 时，浅克隆无法访问历史 commit，导致构建结果可能使用了错误代码。由于构建在 FoundationDB 安装阶段就已失败，该问题尚未暴露，但应当在修复时一并处理。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 的下载 URL 从硬编码 `aarch64` 改为根据 `$(uname -m)` 动态选择对应架构的 RPM。FoundationDB 在 GitHub Releases 上同时提供 `x86_64` 和 `aarch64` 两种 RPM，URL 模式为：
- x86_64: `foundationdb-clients-{VERSION}-1.el9.x86_64.rpm`
- aarch64: `foundationdb-clients-{VERSION}-1.el9.aarch64.rpm`

使用 Shell 变量获取当前架构（`ARCH=$(uname -m)`），并映射到 FoundationDB 的命名约定（`x86_64` → `x86_64`，`aarch64` → `aarch64`）。

### 方向 2（置信度: 中，仅在方向 1 修复后 RPM 仍失败时考虑）
如果 `el9` 的 RPM 与 openEuler 的 glibc/ABI 不兼容（`GLIBC_2.17` 符号依赖无法满足），则放弃 RPM 安装方式，改为从 FoundationDB 官方 Docker 镜像中 `COPY --from` 提取 `fdbcli` 等客户端二进制文件（参考 模式16 的多阶段构建方案），或从源码编译 FoundationDB 客户端库。

### 方向 3（潜伏问题，置信度: 高，模式18）
`git clone --depth 1` 浅克隆与 `git checkout ${VERSION} 2>/dev/null || true` 的组合存在问题：commit hash 在浅克隆中不可访问，且 `|| true` 静默掩盖 checkout 失败。应将 `--depth 1` 改为完整克隆，或使用 `git fetch origin ${VERSION} && git checkout FETCH_HEAD` 先 fetch 再 checkout。

## 需要进一步确认的点
1. FoundationDB 7.3.77 的 el9 RPM 在 openEuler 24.03-LTS-SP3 上是否存在 glibc 版本兼容性问题——方向 1 修复架构检测后，可能需要在上游验证 RPM 的实际可用性。
2. 构建日志显示平台为 x86_64，但 Dockerfile 的其他部分（如 libfuse 编译）是否在 aarch64 CI job 中也能通过——本次提供的日志仅为单架构构建日志，需确认 aarch64 job 的构建结果。
3. 确认 FoundationDB 7.3.77 的 RPM 文件名在 GitHub Releases 中的确切命名格式（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 是否确实存在），避免修正后出现 404（可能触发模式02/27）。

## 修复验证要求
- 修复后需同时在 x86_64 和 aarch64 两套 CI 环境中验证构建通过。
- 确认 FoundationDB RPM 的 GitHub Release URL 在修复后的架构下可正常下载（避免引入 404 新问题）。
- 验证方向 3（模式18 潜伏问题）的修复：确认 `git checkout 22fca04` 在非浅克隆条件下能成功切换至正确 commit。
