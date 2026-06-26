# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 跨发行版RPM依赖不兼容
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6(GLIBC`, `el9`, `foundationdb-clients`, `openEuler`, `rpm -ivh`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm ..." did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
  25 |
--------------------
ERROR: failed to solve: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`
- 失败原因: 从 Apple 下载的 foundationdb-clients RPM 包面向 `el9`（RHEL 9）构建，其 RPM 元数据声明了 `libm.so.6(GLIBC_2.17)(64bit)` 版本化依赖。openEuler 24.03-LTS-SP3 基础镜像的 RPM 数据库中不存在此精确版本化 provides 条目，导致 `rpm -ivh` 依赖解析失败。同时 RPM URL 硬编码了 `aarch64` 架构字符串，在当前 x86_64 构建环境中下载了错误架构的 RPM 包。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`，其中第 22-24 行的 `RUN` 步骤从 GitHub Releases 直接下载并安装了面向 RHEL 9 的 foundationdb-clients RPM。该步骤是构建 3FS 的必要前置依赖（3FS 编译需要 FoundationDB 客户端库），但 RPM 包与 openEuler 基础镜像不兼容，导致 Docker 构建在步骤 5/9 失败。此失败完全由本次 PR 引入。

## 修复方向

### 方向 1（置信度: 高）
从 FoundationDB 官方 RPM 源直接安装，改为从源代码编译 FoundationDB 客户端库，或在 openEuler 容器中通过 `yum` 搜索是否有可用的 FoundationDB 相关包。如果 openEuler 仓库中不存在，可改用 FoundationDB 官方提供的 Docker 多阶段构建方案，从 `foundationdb/foundationdb:7.3.77` 镜像中 `COPY --from` 提取客户端二进制和库文件，完全绕过 RPM 依赖冲突。

### 方向 2（置信度: 中）
使用 `rpm -ivh --nodeps` 强制安装 foundationdb-clients RPM（跳过依赖检查），前提是 openEuler 的基础镜像中实际上存在 `libm.so.6`（GLIBC 2.17+），只是 RPM 数据库未提供版本化 provides 条目。但此方案存在运行时风险，需在容器中验证 foundationdb 客户端功能正常。

### 方向 3（置信度: 中）
将 RPM URL 中的 `aarch64` 替换为 `$(uname -m)` 或 Docker BuildKit 的 `TARGETARCH` 变量，同时将 `el9` 替换为与 openEuler 更兼容的 RPM 包版本。查看 FoundationDB 是否提供无发行版约束的通用 RPM 或 tar.gz 二进制包。

## 需要进一步确认的点
1. openEuler 24.03-LTS-SP3 仓库中是否存在 `foundationdb` 或 `foundationdb-clients` 包（可通过 `yum search foundationdb` 验证）。
2. FoundationDB GitHub Releases 上除 `el9` 外是否提供其他发行版的 RPM（如针对 openEuler/openSUSE 构建的包）。
3. 当前构建日志中 x86_64 环境下载了 aarch64 RPM — 需确认 CI 管道是否为多架构并行构建、aarch64 分支是否也有相同的 GLIBC 依赖错误。
4. 步骤 6/9（git clone --depth 1 + commit checkout）因构建在此前步骤失败而未触发，但该步骤存在已知的 `--depth 1` + commit hash 不兼容问题（历史模式 18），修复当前错误后很可能立即暴露此下一个失败点。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
无需正则 patch 外部源文件。若采用方向 1 的多阶段构建方案，code-fixer 必须：
- 在 openEuler 24.03-LTS-SP3 容器中验证 `COPY --from=foundationdb/foundationdb:7.3.77` 提取的库文件（`libfdb_c.so` 等）与 `/usr/lib64/` 下的 glibc 和其他系统库 ABI 兼容。
- 验证 3FS cmake 构建能正确找到提取的 FoundationDB 头文件和库文件。
