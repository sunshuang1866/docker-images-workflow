# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码不匹配
- 新模式症状关键词: error: Failed dependencies, aarch64, rpm -ivh, x86_64

## 根因分析

### 直接错误
```
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
------
Dockerfile:22
  21 |     
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
  25 |     
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`
- 失败原因: FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构，而 CI 构建环境为 `x86_64`（证据：meson 检测 `Host machine cpu family: x86_64`，rustup 检测 `default host triple is x86_64-unknown-linux-gnu`），导致安装 aarch64 架构的 RPM 包时依赖解析失败。

### 与 PR 变更的关联
PR 新增了 3FS 的 Dockerfile，该 Dockerfile 第 22 行直接硬编码 `aarch64` 作为 FoundationDB 客户端 RPM 包的架构标识。该新建文件是 PR 的核心内容，CI 失败**完全由本次 PR 的变更直接触发**。

此外，Dockerfile 中新写 `Storage/3fs/README.md` 声称支持 `amd64, arm64` 两种架构，但 Dockerfile 整体存在多处架构硬编码问题（第 38-42 行的 clang 库路径也引用了 `aarch64-openEuler-linux-gnu`），使该 Dockerfile 实际上无法在 x86_64 上构建。

## 修复方向

### 方向 1（置信度: 高）
使用 BuildKit 内置的 `TARGETARCH` ARG 动态选择正确的 FoundationDB RPM 架构。在 Dockerfile 头部声明 `ARG TARGETARCH`，然后在 FoundationDB 安装步骤中根据 `TARGETARCH` 的值（`amd64` 或 `arm64`）映射到对应的 RPM 文件名和 URL。需要建立架构映射：`amd64` → `x86_64`（FoundationDB 的命名），`arm64` → `aarch64`。

### 方向 2（置信度: 高）
Dockerfile 中第 38-42 行的 clang 库路径也硬编码了 `aarch64-openEuler-linux-gnu`，同样需要使用 `TARGETARCH` 进行条件化处理，否则在 x86_64 上构建到 cmake 阶段时这些路径也会出错。

### 方向 3（置信度: 中）
FoundationDB RPM 从 `github.com/apple/foundationdb/releases` 下载，依赖 RHEL/CentOS 的 glibc 符号版本（如 `GLIBC_2.17`）。即使在 aarch64 上，openEuler 24.03 的 libm 是否能满足此依赖存疑。建议在修复后、提交前在一个真实的 openEuler aarch64 容器中验证 RPM 能否成功安装（`rpm -ivh --nodeps` 可能作为备选方案，但需确认运行时实际依赖是否满足）。

## 需要进一步确认的点
- FoundationDB `7.3.77` 在 `el9` 上是否有 `x86_64` 架构的 RPM 包（应确认 URL `https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 是否存在）
- openEuler 24.03 的 glibc 版本能否满足 FoundationDB RPM 的 `GLIBC_2.17` 符号版本依赖（在两种架构上均需验证）
- Dockerfile 第 38 行的 `clang-format-14` symlink 在 x86_64 上是否同样适用，还是需要架构区分

## 修复验证要求
验证修复时，必须在 x86_64 和 aarch64 两个架构的 openEuler 24.03-lts-sp3 容器中分别执行完整的 Docker build 流程，确认：
1. FDB RPM 能按架构正确下载和安装
2. clang 库路径 symlink 在不同架构上均正确
3. cmake 构建能完整通过
