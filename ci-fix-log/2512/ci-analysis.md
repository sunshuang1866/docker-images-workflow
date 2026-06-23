# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码错误
- 新模式症状关键词: error: Failed dependencies, aarch64, rpm -ivh, foundationdb-clients

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
ERROR: failed to solve: process ... did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: FoundationDB clients RPM 下载 URL 中硬编码了 `aarch64` 架构，而 CI 构建环境实际为 x86_64（日志中 `#8` Rust 安装步骤输出 `default host triple is x86_64-unknown-linux-gnu`，`#9` meson 编译步骤输出 `Host machine cpu: x86_64`）。aarch64 RPM 包无法在 x86_64 系统上安装，rpm 报告依赖无法满足。

### 与 PR 变更的关联
这是 PR #2512 新增的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 中引入的错误。该 Dockerfile 是本次 PR 的核心新增文件（+69 行），其中 `FoundationDB` 安装步骤（第 22-24 行）的下载 URL 将架构写死为 `aarch64`，没有根据实际构建平台（x86_64 或 aarch64）动态选择对应的 RPM 包，导致在 x86_64 CI 构建节点上失败。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的架构部分从硬编码 `aarch64` 改为动态获取。在 Dockerfile 的 `RUN` 命令中，先通过 `uname -m` 获取当前系统架构（x86_64 或 aarch64），然后映射为 FoundationDB RPM 文件名中对应的架构标识（`x86_64` 或 `aarch64`），构造正确的下载 URL。注意 openEuler:24.03-lts-sp3 基于的 libc 版本也可能与 `el9` RPM 存在兼容性问题，如果替换为正确架构后仍有依赖错误，需考虑改用 `el7` 构建的 FoundationDB RPM 或从源码编译。

### 方向 2（置信度: 中）
如果 FoundationDB 的 el9 RPM 与 openEuler 24.03-lts-sp3 的 glibc/libm 版本根本性不兼容（即使架构正确也会出现 `GLIBC_2.xx not found` 等错误），则需要放弃 RPM 安装方式，改为从 FoundationDB 源码自行编译或使用 FoundationDB 官方 Docker 镜像进行多阶段构建（参考模式16），直接将二进制文件 `COPY --from` 到目标镜像中。

## 需要进一步确认的点
1. FoundationDB 7.3.77 是否发布了 el9 x86_64 RPM（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm`），确认下载 URL 是否存在（需访问 `https://github.com/apple/foundationdb/releases/download/7.3.77/` 验证）。
2. openEuler 24.03-lts-sp3 的 glibc 版本是否兼容 FoundationDB el9 RPM（检查 `ldd --version` 输出，确认 GLIBC_2.17 标记存在）。
3. 如方向 1 中架构修正后依赖仍有问题，需确认 FoundationDB 是否提供 el7 构建（对旧版 glibc 兼容性更好）或 static linked 版本。
4. 模式 18（git 浅克隆与 commit hash checkout 不兼容）也引用了本 PR，当前 CI 日志中 Docker 构建在 FoundationDB 步骤失败后即终止，未覆盖后续的 `git clone` 步骤。如果架构问题修复后 git clone 步骤仍失败，需单独处理模式 18 的问题。
