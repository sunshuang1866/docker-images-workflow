# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构URL硬编码
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6`, `aarch64.rpm`, `GLIBC_2.17`, `foundationdb`, `x86_64`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL ..." did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: FoundationDB 客户端 RPM 的下载 URL 硬编码了 `aarch64` 架构。当前 CI 构建在 x86_64 平台上执行（meson 输出 `Host machine cpu: x86_64`，rustup 输出 `default host triple is x86_64-unknown-linux-gnu`），但 Dockerfile 无条件下载 aarch64 架构的 RPM 包，导致 rpm 因架构不匹配拒绝安装。

### 与 PR 变更的关联
该 Dockerfile 为此 PR 全新添加的文件，整个 FoundationDB 安装步骤是本次 PR 引入的新代码。Dockerfile 中 FoundationDB 下载 URL 缺少架构条件判断逻辑——应当使用 BuildKit 内置变量（如 `TARGETARCH`）或 `uname -m` 检测当前构建架构，从 FoundationDB 的 GitHub Releases 中选择对应架构（`x86_64` 或 `aarch64`）的 RPM 包下载安装。

## 修复方向

### 方向 1（置信度: 高）
在 Dockerfile 的 FoundationDB 安装步骤中使用 BuildKit 的 `TARGETARCH` 内置变量，将硬编码的 `aarch64` 替换为条件选择逻辑：当 `TARGETARCH=amd64` 时下载 `x86_64.rpm`，当 `TARGETARCH=arm64` 时下载 `aarch64.rpm`。FoundationDB 7.3.77 同时发布了两个架构的 RPM 包（`foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 和 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），直接用架构变量拼接 URL 即可。

### 方向 2（置信度: 中）
如果 FoundationDB 在不同架构上的包名差异超过简单的架构后缀替换（例如 `el9` vs `el8`），可考虑从 FoundationDB 官方 Docker 镜像中 `COPY --from` 提取二进制文件，类似于模式16的多阶段构建绕过方法。

## 需要进一步确认的点
1. 确认 FoundationDB 7.3.77 的 x86_64 RPM 包名是否为 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`，与 aarch64 仅在架构后缀上有差异
2. 确认 openEuler 24.03-LTS-SP3 x86_64 容器的 glibc 是否提供 `GLIBC_2.17` 版本的 `libm.so.6` 符号——如果符号缺失，即使下载了正确架构的 RPM 也可能遇到相同的依赖失败
3. PR 中 `git clone --depth 1` 后 `git checkout ${VERSION} 2>/dev/null || true` 的问题（模式18）是否已在本次 diff 中修复——当前 diff 未包含该修复，若 checkout 静默失败可能导致构建出错误版本的 3FS 二进制

## 修复验证要求
- code-fixer 必须在修改后本地执行 `docker build` 验证 FoundationDB RPM 能在 x86_64 和 aarch64 两个架构上成功安装
- 验证 FoundationDB 客户端库（libfdb_c.so）正确安装后 3FS 的 cmake 配置能检测到 FDB 并启用相关特性
