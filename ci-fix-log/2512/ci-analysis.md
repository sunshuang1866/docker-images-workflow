# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM依赖不兼容
- 新模式症状关键词: `error: Failed dependencies:`, `libm.so.6(GLIBC_2.17)`, `foundationdb-clients`, `aarch64`, `x86_64`, `el9`

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
- 失败原因: 3FS Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码为 `aarch64` 架构，而日志中构建环境 CPU 为 `x86_64`（meson 检测 `Host machine cpu: x86_64`，Rust 检测 `default host triple is x86_64-unknown-linux-gnu`），导致在 x86_64 CI 流水线上安装 aarch64 RPM 失败。同时，RPM 来自 RHEL/CentOS 9 (`el9`)，其 glibc 符号版本（`GLIBC_2.17`）与 openEuler 24.03 的 glibc 不完全兼容，即使架构匹配也可能出现依赖错误。

### 与 PR 变更的关联
PR 新增了完整的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行全部为新增），该 Dockerfile 正是触发失败的代码。此前该 PR 已历经多次修复迭代（历史模式 10/11/18 记录了 boost-foundation 包名错误、`.claude/` 路径校验失败、git 浅克隆与 commit hash 冲突等问题），本次出现的 FoundationDB RPM 架构不匹配是新出现的错误。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB 客户端 RPM 的下载 URL 从硬编码架构改为根据构建平台动态选择架构。FoundationDB 7.3.77 在 GitHub Releases 上同时提供 `x86_64` 和 `aarch64` 两种 RPM：
- x86_64: `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`
- aarch64: `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`

可使用 BuildKit 内置的 `TARGETARCH` ARG（值为 `amd64` 或 `arm64`）来动态构造对应架构的 RPM 文件名。注意需将 BuildKit 的 `amd64`/`arm64` 映射为 FoundationDB 的 `x86_64`/`aarch64` 命名。

### 方向 2（置信度: 中）
如果 el9 RPM 在 openEuler 24.03 上即使架构匹配也存在 glibc 依赖问题（`libm.so.6(GLIBC_2.17)` 不可用），则需要放弃 RPM 安装方式，改为从 FoundationDB 官方 Docker 镜像中 `COPY --from` 提取 `fdbcli` 和相关库文件，或多阶段构建方式获取二进制。需要在实际容器中验证 el9 RPM 在 openEuler 上的兼容性后再决定。

## 需要进一步确认的点
1. FoundationDB 7.3.77 的 el9 RPM（x86_64 版本）在 openEuler 24.03-lts-sp3 上是否可成功安装？需在容器中实测 `rpm -ivh foundationdb-clients-7.3.77-1.el9.x86_64.rpm`，确认是否仍有 glibc 版本符号缺失或其他依赖问题。
2. 3FS 项目是否强依赖 FoundationDB 7.3.77 的 RPM 包？是否可以从源码编译或使用其他方式提供 FoundationDB 客户端？
3. 历史模式 18 记录的 git 浅克隆问题（`--depth 1` + commit hash checkout）在当前 Dockerfile 中仍存在（`git clone --recurse-submodules --depth 1 --shallow-submodules`），即使 RPM 问题修复后，该步骤可能仍会触发失败，需一并处理。

## 修复验证要求
1. code-fixer 必须在修复后验证 x86_64 和 aarch64 双架构构建管道均能通过 FoundationDB RPM 安装步骤。
2. 若改用 BuildKit TARGETARCH 动态选择 RPM，需确认 `amd64` → `x86_64` 的映射逻辑在两个 CI 构建节点上都正确。
3. 若放弃 RPM 改为 COPY 方式，需确认从 `foundationdb/foundationdb:7.3.77` 官方镜像 COPY 出的二进制在 openEuler 上可正常运行（包括 libfdb_c.so 等动态库的依赖问题）。
