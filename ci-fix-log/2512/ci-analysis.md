# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨发行版RPM依赖不兼容
- 新模式症状关键词: `error: Failed dependencies`, `GLIBC_2.17`, `is needed by`, `rpm -ivh`, `.el9.`, `foundationdb`

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
- 失败原因: Dockerfile 从 Apple FoundationDB GitHub Releases 下载了 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`，该 RPM 是为 RHEL/CentOS 9（el9）构建的预编译二进制包，依赖 `libm.so.6(GLIBC_2.17)` 版本化符号。openEuler 24.03 的 glibc/libm 不提供该精确的版本化符号（或提供的符号版本不同），导致 `rpm -ivh` 依赖检查失败。

### 与 PR 变更的关联
- 整个 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69行）是本 PR 全新新增的文件，失败步骤由 PR 首次引入。
- 该 RUN 步骤试图在 openEuler 基础镜像上直接安装 FoundationDB 的 el9 预编译 RPM，未考虑跨发行版二进制兼容性问题。

### 附加发现
- 日志显示 Rust 安装时 `default host triple is x86_64-unknown-linux-gnu`，但 Dockerfile 中 FoundationDB RPM URL 硬编码了 `aarch64` 架构。当前失败发生在依赖解析阶段，但即便通过 `--nodeps` 绕过，也将在 x86_64 构建 job 中遇到架构不匹配问题。
- 历史知识库（模式18）同时记录了本 PR 内 `git clone --depth 1` + commit hash checkout 不兼容问题，该问题在当前日志中未触发（构建在第 5/9 步 FoundationDB 步骤已失败，第 6/9 步 git clone 未执行），但需一并关注。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB 客户端的安装方式从"下载预编译 el9 RPM 并 rpm -ivh"改为从 FoundationDB 官方容器镜像中 COPY 二进制文件，或从 FoundationDB 源码编译。如果必须使用预编译 RPM，需确认 FoundationDB 是否提供适用于 openEuler 的包或通用 Linux 二进制 tarball，而非 el9 专用 RPM。参考模式16（`grafana-agent`）的多阶段构建方案：`COPY --from=fdb-source`。

### 方向 2（置信度: 中）
若 FoundationDB 对 glibc ABI 要求不高（仅版本化符号声明差异），可尝试 `rpm -ivh --nodeps` 安装（跳过 RPM 依赖检查），并在 ENV LD_LIBRARY_PATH 中补充必要的库路径。但此方案有运行时崩溃风险，因为 openEuler 的 glibc 可能确实缺少实际需要的符号。

### 方向 3（置信度: 低）
将 Dockerfile 中硬编码的 `aarch64` 改为根据构建目标动态选择架构的变量，同时在 FoundationDB Release 页面确认是否有 x86_64 的 RPM 包可用（当前 URL 仅引用 aarch64 包）。

## 需要进一步确认的点
1. **FoundationDB 官方容器镜像**：`foundationdb/foundationdb:7.3.77` 是否存在，其内部二进制路径是什么。
2. **FoundationDB Releases 页面**：https://github.com/apple/foundationdb/releases/tag/7.3.77 是否提供通用 Linux tarball（非 RPM）或 x86_64 RPM。
3. **openEuler glibc 版本**：`openeuler/openeuler:24.03-lts-sp3` 中的 glibc 版本和提供的符号版本清单，以确认是否仅为声明层面不匹配还是真正的 ABI 不兼容。
4. **历史知识库模式18**：本 PR 的 Dockerfile 第 29-30 行 `git clone --depth 1` + `git checkout ${VERSION}` 在本次日志中未触发，但若 FoundationDB 步骤修复后，该步骤大概率会因浅克隆无法访问历史 commit 而失败，需同步修复。

## 修复验证要求
修复方向1（多阶段构建 COPY 方案）的验证步骤：
- code-fixer 必须在修复后验证 `foundationdb/foundationdb:7.3.77` 官方镜像的二进制文件在 openEuler 24.03-lts-sp3 基础镜像中能正常运行（LD_LIBRARY_PATH 正确、库依赖可解析）。
- 若改为使用 FoundationDB 通用 tarball 安装，需在 openEuler 24.03-lts-sp3 容器中实际执行安装和 `fdbcli --version` 验证。
