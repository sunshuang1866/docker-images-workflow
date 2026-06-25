# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM架构硬编码
- 新模式症状关键词: Failed dependencies, harcoded aarch64, foundationdb, rpm -ivh, el9

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
------
Dockerfile:22
--------------------
  22 | >>> RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm && \
  23 | >>>     rpm -ivh /tmp/fdb-clients.rpm && \
  24 | >>>     rm -f /tmp/fdb-clients.rpm
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB RPM 下载 URL 硬编码了 `aarch64` 架构，而 CI 实际构建环境为 x86_64（日志中 Rust 三元组为 `x86_64-unknown-linux-gnu`，meson 输出 `Host machine cpu family: x86_64`）。x86_64 系统上安装 aarch64 的 RPM 包导致 `rpm -ivh` 依赖解析失败。

### 与 PR 变更的关联
PR 新增了 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`（共 69 行），该 Dockerfile 中的第 22 行 `RUN` 指令直接包含硬编码的 `aarch64` 架构 RPM URL。此次失败完全由 PR 引入的新代码触发。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB RPM 下载 URL 中的硬编码架构 `aarch64` 替换为构建时动态获取的目标架构。Docker BuildKit 提供 `TARGETARCH` 内置 ARG（值为 `amd64` 或 `arm64`），但在 `RUN` 指令中使用需先声明 `ARG TARGETARCH`。注意避免使用 `BUILDARCH`（BuildKit 预定义变量，在 RUN 中重新赋值无效，参考模式09）。

FoundationDB GitHub Releases 中同时提供了 x86_64 和 aarch64 两种 RPM，URL 格式如下：
- x86_64: `.../foundationdb-clients-7.3.77-1.el9.x86_64.rpm`
- aarch64: `.../foundationdb-clients-7.3.77-1.el9.aarch64.rpm`

需要将 Docker BuildKit 的 `amd64`/`arm64` 映射为 FoundationDB 使用的 `x86_64`/`aarch64` 架构标识。

### 方向 2（置信度: 中）
如果 FoundationDB `el9` RPM 在 openEuler 24.03 上即使架构匹配也存在 glibc 版本兼容性问题（`libm.so.6(GLIBC_2.17)` 依赖），可考虑不通过 RPM 安装，改为从 FoundationDB 官方 Docker 镜像中多阶段 `COPY` 二进制文件，或手动编译 FoundationDB 客户端库。

## 需要进一步确认的点
1. 即使修复架构问题后，需确认 FoundationDB `el9` RPM 在 openEuler 24.03-LTS-SP3 上的 `libm.so.6(GLIBC_2.17)` 版本符号是否实际可用，避免依赖解析同样失败。
2. 历史模式 #18 指出同一 Dockerfile 中 `git clone --depth 1` 后 `git checkout ${VERSION} 2>/dev/null || true` 存在浅克隆与 commit hash checkout 不兼容的问题。当前构建在步骤 5/9 即失败，步骤 6/9（git clone）尚未执行，修复 FDB 问题后可能暴露该下游问题。
3. 历史模式 #10 指出同一 Dockerfile 存在 `boost-foundation` 运行时包名问题及缺少构建依赖。当前构建未到达该阶段，修复后需一并验证。
