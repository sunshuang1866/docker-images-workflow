# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码
- 新模式症状关键词: Failed dependencies, aarch64, x86_64, rpm, rpmlib

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
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构后缀，而 CI 当前构建作业运行在 x86_64 架构上（证据：Rust 目标三元组为 `x86_64-unknown-linux-gnu`，Meson 报告 `Host machine cpu family: x86_64`），导致 `rpm -ivh` 因架构不匹配而解析依赖失败。

### 与 PR 变更的关联
此 Dockerfile 是本次 PR 全新添加的文件（69 行新增）。失败直接由该新增 Dockerfile 第 22 行中 FoundationDB RPM URL 的架构硬编码 `aarch64` 引起。该文件随本次 PR 首次引入仓库，因此失败 100% 与本次 PR 变更相关。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的 `aarch64` 替换为 BuildKit 预定义变量 `TARGETARCH` 动态选择架构对应的 RPM 文件名：
- `TARGETARCH=amd64` → `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`
- `TARGETARCH=arm64` → `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`

使用 shell 条件或变量映射表实现架构到 RPM 文件名的转换。

### 方向 2（可选，置信度: 中）
若 FoundationDB 不提供 x86_64 的 `.el9` RPM，可改用 FoundationDB 官方 Docker 镜像多阶段构建方式（类似历史模式16：从 `foundationdb/foundationdb:7.3.77` 镜像中 `COPY` 客户端二进制文件），完全绕过 RPM 安装。

## 需要进一步确认的点
1. `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 在 GitHub Releases 中是否确实存在（与 aarch64 版本同目录）。
2. FoundationDB 7.3.77 的 `el9` RPM 在 openEuler 24.03-LTS-SP3 上是否有 glibc 版本兼容性问题——当前错误是架构不匹配引起的，修复架构后还需验证 x86_64 RPM 是否能正确安装，避免修复后出现新一轮 glibc 版本依赖失败。
3. `gtest-devel`、`gmock-devel`、`clang-tools-extra`、`libdwarf-devel`、`gperftools-devel` 等包在 openEuler 24.03-LTS-SP3 yum 仓库中是否确实可用（日志中 yum install 步骤未报错这些包，但 `.claude/CLAUDE.md` 曾注明它们不可用，需确认仓库已更新）。

## 修复验证要求
1. 修复后，Code Fixer 必须分别在 x86_64 和 aarch64 两个架构的 CI 作业中验证 FoundationDB RPM 安装步骤均通过。
2. 若采用方向 2（多阶段构建），需从 `foundationdb/foundationdb:7.3.77` 官方镜像确认 `fdbcli`、`libfdb_c.so` 等客户端文件的准确路径后再编写 COPY 指令。
3. 修复后建议本地执行 `docker build` 完成整个 Dockerfile 的所有 9 个步骤，确保后续 cmake 编译步骤（步骤 6）不会因 glibc 或其他库版本差异引入新的构建错误。
