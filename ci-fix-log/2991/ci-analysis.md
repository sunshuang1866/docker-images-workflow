# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: CI 的 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在通过 `dnf` 从 `repo.openeuler.org` 下载 RPM 包时，多个包（`git-core`、`gcc-c++`、`guile`）遭遇 HTTP/2 流中断（Curl error 92），其中 `guile` 在重试耗尽后彻底失败，导致整个 `dnf install` 命令以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准的 vvenc Dockerfile（安装构建依赖 → git clone → cmake 构建 → 安装），Dockerfile 中 `dnf install` 命令本身语法正确。失败发生在 `dnf` 从 openEuler 官方仓库下载依赖包的阶段，属于 CI 构建节点与软件仓库之间的网络/HTTP/2 协议层问题，并非 Dockerfile 或 vvenc 源码问题。

## 修复方向

### 方向 1（置信度: 中）
重试 CI 构建。该失败是 `repo.openeuler.org` 与 aarch64 CI runner 之间的 HTTP/2 传输层间歇性故障，多次 `Curl error (92)` 表明这是网络层的不稳定问题。重新触发 CI 流水线，若仓库侧网络恢复正常，构建应能通过。

### 方向 2（置信度: 低）
若重试持续失败，可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf` 的重试/超时配置（如 `echo 'max_retries=10' >> /etc/dnf/dnf.conf`），或切换到 openEuler 的其他镜像站点。但这属于对网络问题的 workaround，非根本解决方案。

## 需要进一步确认的点
1. `repo.openeuler.org` 在失败时间段是否存在已知的 HTTP/2 服务端问题或 CDN 节点异常
2. CI 的 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否稳定
3. 同一 PR 的 x86_64 构建 job 是否也失败（日志中仅包含 aarch64 job，需确认 x86_64 侧情况）
4. 近期的其他 PR（使用相同基础镜像 `openeuler:24.03-lts-sp4` 的构建）是否也出现同类 `Curl error (92)` 问题
