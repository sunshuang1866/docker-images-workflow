# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: OpenEuler仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, dnf install, aarch64

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: CI aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）在 `dnf install` 阶段从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 aarch64 RPM 包时，多个包遭遇 HTTP/2 协议层 stream 错误（Curl error 92: `Stream error in the HTTP/2 framing layer`），部分包经 dnf 自动重试后成功，但 `guile-5:2.2.7-6.oe2403sp4.aarch64` 耗尽所有 mirror 重试后最终失败，导致整个安装步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 改动无关**。PR 仅新增了一个标准的 Dockerfile（`dnf install` 安装常用构建工具链 git/gcc/gcc-c++/make/cmake）、更新了 README.md、image-info.yml 和 meta.yml。`dnf install` 命令本身语法正确，失败完全由 CI 构建节点与 `repo.openeuler.org` 之间的 HTTP/2 网络传输问题导致。`gcc-c++` 包在两次不同 stream（39、51）上均失败，进一步说明这是服务端或网络中间件的 HTTP/2 协议处理异常，而非 PR 代码问题。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建**。该失败为间歇性网络基础设施问题（HTTP/2 stream 错误），与 PR 代码无关。等待 `repo.openeuler.org` 服务端 HTTP/2 问题恢复后重试构建，大概率直接通过。

### 方向 2（置信度: 低）
**降级到 HTTP/1.1**。如果 `repo.openeuler.org` 的 HTTP/2 问题持续存在，可考虑在 Dockerfile 的 `dnf install` 前添加 curl 配置使 dnf 使用 HTTP/1.1（如设置 `http2=false` 或通过 `echo "http2=false" >> /etc/dnf/dnf.conf`），绕过 HTTP/2 协议层的 stream 错误。但此方向会降低下载效率，仅作为临时 workaround。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 HTTP/2 服务在 aarch64 包下载路径上是否存在持续性问题（可通过在 CI 环境外手动 `curl --http2` 下载同名 RPM 包验证）
- 确认同一 PR 的 x86_64 构建 job 是否通过（日志中仅提供了 aarch64 job 的日志）：若 x86_64 也失败且有类似 Curl error 92，则确认是 openEuler 仓库侧问题；若 x86_64 通过，则可能仅是 aarch64 仓库节点的 HTTP/2 实现有 bug
- 确认是否存在仅 aarch64 构建环境中 dnf/curl 的 HTTP/2 兼容性问题（如 curl 版本过旧触发已知的 HTTP/2 协议 bug）
