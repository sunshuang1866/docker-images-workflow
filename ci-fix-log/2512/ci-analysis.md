# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码
- 新模式症状关键词: error: Failed dependencies, rpm -ivh, aarch64, x86_64, foundationdb

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
    rpm -ivh /tmp/fdb-clients.rpm && \
    rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL ..." did not complete successfully: exit code: 1
------
Dockerfile:22
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码为 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），但当前 CI 构建环境为 x86_64（日志中 rustup 检测到 `x86_64-unknown-linux-gnu`）。跨架构 RPM 无法安装，rpm 依赖解析失败。

### 与 PR 变更的关联
- 此失败由 PR 直接引入。该 PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（全新文件，69 行），其中第 22 行硬编码了 aarch64 架构的 FoundationDB RPM URL。
- Dockerfile 未使用 BuildKit 内置变量（如 `TARGETARCH`）或 shell 命令（`uname -m`）来动态选择对应架构的 RPM，导致 x86_64 构建作业无法正确安装。
- 该 Dockerfile 还存在其他潜在问题（详见"需要进一步确认的点"），但当前构建在步骤 5/9 即失败，后续步骤未被验证。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的 `aarch64` 替换为架构感知变量（BuildKit 的 `TARGETARCH` 或 `$(uname -m)`），使同一 Dockerfile 能同时支持 x86_64 和 aarch64 构建。需先在 Dockerfile 中声明 `ARG TARGETARCH`，再根据架构值构造正确的 RPM 文件名（x86_64 架构对应 `x86_64`，aarch64 架构对应 `aarch64`）。

### 方向 2（置信度: 中）
FoundationDB 客户端 RPM 为 `el9`（RHEL/CentOS 9）构建。即使修复架构匹配问题后，在 openEuler 24.03 上 RPM 的依赖（如特定版本的 glibc capability string）可能仍不兼容。如果 RPM 方式持续不可靠，可考虑改用 FoundationDB 官方提供的预编译 Linux 二进制 tarball（`fdbserver.x86_64` / `fdbcli.x86_64` 等）直接 `COPY` 或从源码编译。

## 需要进一步确认的点
1. **上游 FoundationDB 是否提供 x86_64 RPM**：需确认 `https://github.com/apple/foundationdb/releases/download/7.3.77/` 下是否存在 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`，以及该 RPM 在 openEuler 24.03 环境中的实际依赖兼容性。
2. **clang-tools-extra 等包可用性**：Dockerfile 第 1 个 `yum install` 中列出的 `clang-tools-extra`、`gmock-devel`、`gtest-devel`、`libdwarf-devel`、`gperftools-devel` 据历史模式确认在 openEuler 上不存在或包名不同。虽然当前 `yum install` 步骤未直接报错（yum 可能跳过不存在包或以近似包替代），但后续 `cmake` 构建阶段可能因缺少这些依赖而失败。需在 x86_64 构建环境中逐包验证。
3. **Rust 链接器依赖**：Dockerfile 安装 Rust 工具链后，3FS 的 cmake 构建可能依赖 Rust 编译一些 crate。需确认容器内 cmake 能找到 `rustc`/`cargo` 并能解析所有 Rust 依赖。
4. **git shallow clone 与 commit hash checkout**：Dockerfile 使用 `git clone --depth 1` 然后用 `git checkout ${VERSION} 2>/dev/null || true`，其中 `|| true` 会静默掩盖 checkout 失败。历史模式 #18 已记录此问题，可能在构建通过 FoundationDB 步骤后暴露。
5. **多个 sed 修改的上游兼容性**：Dockerfile 中多处 `sed -i` 修改 3FS 和 rocksdb 的 CMakeLists.txt，需确认这些修改在目标 commit `22fca04` 上仍然适用。
6. **RPM 下载失败时的错误处理**：`rpm -ivh` 失败时，前面的 `curl` 已成功下载 RPM 到 `/tmp/fdb-clients.rpm`。若需要重试逻辑，应完善错误处理。

## 修复验证要求
- 修复后需在 **x86_64 和 aarch64 两个架构** 上分别执行完整 Docker build 验证。
- 需确认 FoundationDB 7.3.77 的 RPM（对应架构版本）在 openEuler 24.03-lts-sp3 容器内可直接 `rpm -ivh` 安装，且所有依赖自动满足；若 RPM 依赖无法满足，需改用二进制包或源码编译方案。
- 在 x86_64 构建环境验证时，需特别确认 `clang-tools-extra`、`gtest-devel`、`gmock-devel` 等包的实际可用包名（参考 openEuler 24.03 仓库），如有缺失需调整 yum install 命令或配置替代源。
- 若 FoundationDB 7.3.77 在 GitHub Releases 中确实未提供 x86_64 RPM，需从 FoundationDB 官方文档确认替代安装方式并在 Dockerfile 中实现。
