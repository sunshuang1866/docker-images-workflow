# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 外源RPM不兼容openEuler
- 新模式症状关键词: Failed dependencies, GLIBC_2.17, is needed by, el9, rpm -ivh

## 根因分析

### 直接错误
```
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`（FoundationDB RPM 安装步骤）
- 失败原因: FoundationDB 官方提供的 RPM 包 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm` 是为 RHEL/CentOS 9 (`el9`) 构建的，其动态链接依赖 `libm.so.6(GLIBC_2.17)` 版本的符号。openEuler 24.03-LTS-SP3 的 glibc 不提供该符号版本（或使用了不同的版本命名方案），导致 `rpm -ivh` 的依赖检查失败。

### 与 PR 变更的关联
PR #2512 新增了完整的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（69 行），其中第 22-24 行硬编码了 FoundationDB RPM 的下载和安装命令。该 RPM URL 指向一个针对 RHEL 9 构建的预编译二进制包，与 openEuler 的基础镜像 ABI 不兼容。此失败由本次 PR 的改动直接触发。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB 的安装方式从"下载预编译 RPM"改为**多阶段构建中从 FoundationDB 官方 Docker 镜像提取二进制文件**（参照历史模式16 的修复思路）。FoundationDB 官方镜像（如 `foundationdb/foundationdb:7.3.77`）内的二进制文件是静态链接或包含必要运行库的，直接 `COPY --from` 可绕过 RPM 依赖检查问题。

### 方向 2（置信度: 中）
从 RPM 中手动提取文件而不走 `rpm -ivh` 的依赖检查：使用 `rpm2cpio` 解包 RPM 的内容，将二进制和库文件手动放到系统路径中。但此方式存在运行时风险——如果运行时的 glibc 确实缺少必要的符号版本，程序仍会在运行时崩溃。需在 openEuler 容器中实际验证二进制文件能否正常执行。

### 方向 3（置信度: 低）
从 FoundationDB 源码编译客户端库。FoundationDB 使用 CMake + Make 构建，但其构建依赖较多且编译耗时较长，不如方向 1 高效。

## 需要进一步确认的点
1. CI 构建目标架构：日志中步骤 `#9`（fuse 编译）显示 `Host machine cpu: x86_64`，而 RPM URL 中硬编码了 `aarch64`。需确认当前失败发生在 x86_64 还是 aarch64 构建 job 中，以及 Dockerfile 是否需要根据 `TARGETARCH` 动态选择 RPM URL。
2. 该 PR 在历史记录（模式10、模式18）中曾出现过其他构建错误（`boost-foundation` 包名不存在、`git clone --depth 1` 与 commit hash checkout 不兼容等），需确认这些前置问题是否已在当前 Dockerfile 版本中修复。当前日志中步骤 1-9 均成功，但若后续步骤（编译 3FS 本体）因这些问题仍然存在，修复 RPM 后可能继续失败。
3. FoundationDB 7.3.77 的 RPM 是否提供 x86_64 版本——当前 URL 仅指向 aarch64，若 x86_64 构建 job 需要对应架构的 RPM，可能需要不同的下载 URL。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用——本失败不涉及正则 patch 外部源文件。
