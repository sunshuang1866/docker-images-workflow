# CI 失败分析报告

## 基本信息
- PR: #2512 — Add 3FS Image
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 硬编码架构RPM
- 新模式症状关键词: `error: Failed dependencies`, `libm.so.6(GLIBC_`, `foundationdb-clients`, `aarch64`, `rpm -ivh`

## 根因分析

### 直接错误
```
#10 [5/9] RUN curl -sL --retry 5 -o /tmp/fdb-clients.rpm https://github.com/apple/foundationdb/releases/download/7.3.77/foundationdb-clients-7.3.77-1.el9.aarch64.rpm &&     rpm -ivh /tmp/fdb-clients.rpm &&     rm -f /tmp/fdb-clients.rpm
#10 0.509 error: Failed dependencies:
#10 0.509 	libm.so.6(GLIBC_2.17)(64bit) is needed by foundationdb-clients-7.3.77-1.aarch64
#10 ERROR: process "/bin/sh -c ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile:22`
- 失败原因: Dockerfile 中 FoundationDB 客户端 RPM 的下载 URL 硬编码了 `aarch64` 架构后缀，而当前 CI 构建环境运行在 `x86_64` 架构上（日志中 `rustup` 步骤输出 `default host triple is x86_64-unknown-linux-gnu` 可证实）。`rpm -ivh` 尝试安装 aarch64 包时因目标系统为 x86_64 而无法满足 `libm.so.6(GLIBC_2.17)(64bit)` 的架构依赖。

### 与 PR 变更的关联
本次 PR 新增的 `Storage/3fs/22fca04/24.03-lts-sp3/Dockerfile` 第 22 行直接包含了硬编码架构的 RPM URL。该 Dockerfile 为此 PR 全新引入（+69 行），CI 失败由该文件直接触发。其他文件变更（`.claude/` 目录重命名、文档更新等）与此失败无关。

## 修复方向

### 方向 1（置信度: 高）
Dockerfile 中 FoundationDB 客户端 RPM 的下载 URL 应根据目标架构动态选择，而非硬编码 `aarch64`。FoundationDB 7.3.77 在 GitHub Releases 上同时提供了 `x86_64` 和 `aarch64` 两种 RPM，需在 `RUN` 指令中通过 BuildKit 内置 ARG（如 `TARGETARCH`）或 shell 条件判断来构造正确的 URL。例如，x86_64 构建时下载 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm`。

### 方向 2（置信度: 中）
若 FoundationDB 的 EL9 RPM 在 openEuler 24.03 上即使架构匹配也存在 glibc 版本兼容性问题，则需考虑从 FoundationDB 源码编译客户端，或改用 `foundationdb-server` 官方 Docker 镜像的多阶段构建方式 `COPY` 二进制文件。但当前日志仅暴露架构不匹配问题，glibc 兼容性需修复方向 1 后验证。

## 需要进一步确认的点
- 确认 FoundationDB 7.3.77 的 `x86_64` RPM 在 openEuler 24.03-LTS-SP3 上能否正常安装（glibc 版本兼容性）。
- 确认 CI 是否会同时触发 x86_64 和 aarch64 两架构的构建 job；若会，需在 Dockerfile 中为两架构分别处理 RPM URL。

## 修复验证要求
- code-fixer 修改 RPM URL 架构选择逻辑后，需验证 FoundationDB 7.3.77 在 GitHub Releases 上确实存在 `foundationdb-clients-7.3.77-1.el9.x86_64.rpm` 文件（访问 https://github.com/apple/foundationdb/releases/tag/7.3.77 确认）。
- 修复后需在 x86_64 和 aarch64 两个架构的 openEuler 24.03 容器中分别验证 RPM 安装成功。
