# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 架构硬编码RPM URL
- 新模式症状关键词: error: Failed dependencies, libm.so.6, foundationdb-clients, aarch64, rpm -ivh, x86_64

## 根因分析

### 直接错误
```
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22-24`
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 下载 URL 硬编码为 `aarch64` 架构（`foundationdb-clients-7.3.77-1.el9.aarch64.rpm`），但 CI 构建环境实际运行在 x86_64 架构上（日志中 rustup 显示 `default host triple is x86_64-unknown-linux-gnu`，fuse meson 构建显示 `Host machine cpu family: x86_64`），导致 RPM 依赖解析在跨架构场景下失败。

### 与 PR 变更的关联
PR #2512 新增了完整的 3FS Dockerfile（`Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile`），该文件第 22 行的 FoundationDB RPM 安装步骤直接将架构硬编码为 `aarch64`，未使用 BuildKit 的 `BUILDARCH` 变量或其他架构检测机制来动态选择正确的 RPM 包。此错误由本次 PR 直接引入。

## 修复方向

### 方向 1（置信度: 高）
将 FoundationDB 客户端 RPM 下载 URL 中的 `aarch64` 改为使用 BuildKit 预定义变量（如 `TARGETARCH`）动态生成，使 Dockerfile 能同时支持 x86_64 和 aarch64 两个目标架构：
- x86_64 构建时下载 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`
- aarch64 构建时下载 `foundationdb-clients-7.3.77-1.el9.aarch64.rpm`
- 需在 Dockerfile 顶部声明 `ARG TARGETARCH` 以启用该变量。

### 方向 2（置信度: 中）
即使修正了架构选择，FoundationDB 的 `el9`（RHEL 9）RPM 包可能与 openEuler 24.03 的 glibc 版本符号不兼容。如果 x86_64 的 `el9` RPM 仍报依赖错误，则需考虑：
- 改用 FoundationDB 官方提供的多阶段 Docker 构建方式，从 `foundationdb/foundationdb:7.3.77` 镜像中 `COPY --from` 提取客户端二进制，绕过 RPM 依赖问题。
- 或从 FoundationDB 源码编译客户端库。

## 需要进一步确认的点
1. 确认 FoundationDB `7.3.77-1.el9.x86_64.rpm` 在 openEuler 24.03-LTS-SP3 x86_64 容器中是否能正常安装（glibc 符号版本兼容性）。
2. 确认 CI 构建矩阵是否同时覆盖 x86_64 和 aarch64 两个架构——若覆盖，修复后还需验证 aarch64 架构构建。
3. 确认 `ARB VERSION=22fca04` 对应的 git commit 在上游 `deepseek-ai/3fs` 仓库中是否可访问（历史模式18曾指出 `--depth 1` 浅克隆与 commit hash checkout 不兼容的问题——虽当前日志未触发该错误，但 Dockerfile 第 29-31 行的 `git clone --depth 1` + `git checkout ${VERSION} 2>/dev/null || true` 可能在其他构建环境/架构下暴露此问题，建议一并关注）。
