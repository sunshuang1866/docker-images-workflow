# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RHEL RPM openEuler依赖不兼容
- 新模式症状关键词: error: Failed dependencies, libm.so.6(GLIBC_2.17), foundationdb-clients, el9, rpm -ivh

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
------ 
Dockerfile:22
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: FoundationDB 官方提供的 RPM 包 (`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`) 是为 RHEL/CentOS 9 (`el9`) 构建的，其 RPM 依赖声明中包含 `libm.so.6(GLIBC_2.17)(64bit)`，但 openEuler 24.03 的 glibc RPM 提供的符号依赖格式与该 RPM 期望的格式不匹配，导致 `rpm -ivh` 依赖解析失败。

### 与 PR 变更的关联
PR 新增了完整的 3FS Dockerfile（`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`），其中第 22-24 行是本次 PR 引入的 FoundationDB 客户端 RPM 安装步骤。该步骤使用的 RPM 来自上游 Apple/FoundationDB 的 GitHub Release，该 RPM 专为 RHEL 9 构建，与 openEuler 基础镜像不兼容。**此失败完全由本次 PR 的代码变更触发。**

## 修复方向

### 方向 1（置信度: 高）
使用 `rpm -ivh --nodeps` 跳过 RPM 依赖检查，直接安装 FoundationDB 客户端。由于 FoundationDB 客户端的实际运行依赖（libm.so.6 等）在 openEuler 24.03 系统上客观存在（只是 RPM 元数据层面的 provides 字符串不匹配），`--nodeps` 可绕过此元数据校验。安装后需在容器内手动验证 `fdbcli` 可正常执行。

### 方向 2（置信度: 中）
改用 FoundationDB 的官方二进制 tarball 而非 RPM 安装。从 FoundationDB GitHub Release 下载对应架构的 `.tar.gz` 包，解压后直接复制二进制文件到 `/usr/local/bin`。这完全避免了 RPM 依赖解析问题。需确认 FoundationDB 7.3.77 是否提供 tarball 格式的发布制品。

## 需要进一步确认的点
1. 验证 `rpm -ivh --nodeps` 安装后，`fdbcli` 及相关 .so 库在 openEuler 24.03 aarch64 容器内是否可以正常运行（即只需确认实际 ELF 动态链接依赖均能满足，而不仅是 RPM 元数据问题）。
2. 确认 FoundationDB 7.3.77 在 GitHub Release 中是否提供 aarch64 架构的 tar.gz/tar.bz2 二进制包，以评估方向 2 的可行性。
3. 确认 3FS 对 FoundationDB 客户端版本是否有精确要求（是否必须 7.3.77，或可接受其他版本），以便评估是否有其他兼容的 FoundationDB 客户端安装方式。
