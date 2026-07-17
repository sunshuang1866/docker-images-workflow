# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, stream was not closed cleanly, repo.openeuler.org

## 根因分析

### 直接错误

```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 构建节点: `ecs-build-docker-aarch64-04-sp`（aarch64 架构）
- 失败原因: CI 构建过程中，`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库镜像出现 HTTP/2 协议层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致多个 RPM 包下载中途断开。dnf 对 `git-core` 和 `gcc-c++` 的重试成功，但 `guile` 包在耗尽所有 mirror 重试后仍下载失败，导致整个 `dnf install` 命令返回退出码 1。

### 与 PR 变更的关联

**本次失败与 PR 代码变更无关。** PR 新增的 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`）中 `dnf install -y git gcc gcc-c++ make cmake` 命令本身语法正确、包名有效。失败原因是 CI 运行时 `repo.openeuler.org` 的 aarch64 仓库镜像出现瞬态 HTTP/2 协议错误，属于 CI 基础设施/网络层面的问题。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试（re-run / re-trigger）。** 本次失败为 `repo.openeuler.org` 仓库镜像的瞬态 HTTP/2 网络错误。`git-core` 和 `gcc-c++` 在 mirror 重试后均下载成功，仅 `guile` 碰巧在重试耗尽前未能成功。这表明网络问题并非持续性的仓库宕机，而是间歇性的 TCP/HTTP/2 流中断。只需重新触发 CI 构建，在仓库恢复正常的时间窗口内即可通过。

### 方向 2（置信度: 低）
**如果重试后仍然失败**，可能是 `repo.openeuler.org` 仓库侧的持续性故障（如 CDN 节点异常、HTTP/2 配置变更导致 aarch64 节点兼容性问题）。此时需要联系 openEuler 基础设施团队排查仓库镜像的 HTTP/2 服务状态，或在 Dockerfile 中将 `dnf install` 的回退重试机制增强（如添加 `--setopt=retries=10` 增加重试次数）。

## 需要进一步确认的点

- 无需进一步确认。日志证据充分：多个 Curl error (92) 均指向 `repo.openeuler.org` 的 HTTP/2 framing layer，且失败口是 `guile` 包下载重试耗尽，符合典型的仓库镜像瞬态故障特征。
- 若多次重试 CI 后仍持续失败，需要确认 `repo.openeuler.org` 在 aarch64 CI 环境中的 HTTP/2 连通性是否有持续性问题。

## 修复验证要求

无需验证。本次为 infra-error，无需修改代码，Code Fixer Agent 无需处理。
