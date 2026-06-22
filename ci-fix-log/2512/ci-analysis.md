# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码不匹配
- 新模式症状关键词: Failed dependencies, GLIBC, aarch64, rpm -ivh, foundationdb-clients, el9, architecture mismatch

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  21 |     
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
  25 |     
--------------------
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`:22
- 失败原因: FoundationDB RPM 下载 URL 硬编码为 `aarch64` 架构，而本次 CI 构建运行在 `x86_64` 架构上（日志中步骤 #8 显示 `default host triple is x86_64-unknown-linux-gnu`，步骤 #9 显示 `Host machine cpu family: x86_64`），导致架构不匹配，RPM 依赖检查失败。

### 与 PR 变更的关联
本次 PR 新增了整个 3FS Dockerfile（`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`），其中的 FoundationDB RPM 安装步骤（第 22-24 行）直接导致了此次失败。该 Dockerfile 是全新文件，错误与 PR 变更强相关。

还需注意：即使修正了架构问题，该 RPM 是为 RHEL/CentOS 9 (`el9`) 构建的，openEuler 24.03-LTS-SP3 的 glibc 版本可能与 `GLIBC_2.17` 符号版本要求不完全兼容（aarch64 平台）。这可能意味着在 aarch64 架构上该 RPM 也无法直接安装，需进一步验证。

## 修复方向

### 方向 1（置信度: 高）
FoundationDB RPM URL 需根据构建架构动态选择。利用 BuildKit 内置的 `TARGETARCH` ARG（值为 `amd64` 或 `arm64`）构造条件分支：当 `TARGETARCH=amd64` 时下载 `x86_64` 架构 RPM，当 `TARGETARCH=arm64` 时下载 `aarch64` 架构 RPM。同时需验证 openEuler 的 glibc 是否满足 FoundationDB RPM 的依赖要求，若不满足则需改用从源码构建 FoundationDB 客户端库或找到 openEuler 原生包替代方案。

### 方向 2（置信度: 中）
完全绕过 FoundationDB RPM 安装，改为从 FoundationDB 源码编译客户端库（`fdb_c` 和 `libfdb_c`），确保与 openEuler 的 glibc 和系统库兼容。这需要检查 FoundationDB 7.3.77 的构建依赖（需要 cmake、OpenJDK、Mono 等），构建时间较长但架构兼容性最好。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP3 aarch64 的 glibc 版本是否实际提供 `GLIBC_2.17` 符号（`libm.so.6`）——这可能仅是架构不匹配导致的第一条错误，在正确架构上可能不存在此问题
2. FoundationDB 7.3.77 是否发布 `x86_64` 架构 RPM，以及其 URL 格式（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm`）
3. 3FS 项目是否强依赖 FoundationDB 7.3.77 客户端，以及是否有 openEuler 提供的 FoundationDB 原生包可替代 RPM 安装
4. 知识库中已记录的该 PR 其他问题（模式10：boost-foundation 包名不存在、模式18：git 浅克隆 + commit hash checkout 不兼容）在此次构建中尚未触发（构建在步骤 5/9 已失败），后续修复时需一并处理

## 修复验证要求
code-fixer 在修改 Dockerfile 后，必须：
1. 分别对 `x86_64` 和 `aarch64` 两个架构验证 FoundationDB RPM 能否成功安装
2. 若改用动态架构选择，需在本地同时模拟两个架构的构建验证 URL 正确性
3. 若 RPM 安装方案在 openEuler 上存在 glibc 兼容性问题，需回退到源码编译方案并验证客户端库能正常链接
