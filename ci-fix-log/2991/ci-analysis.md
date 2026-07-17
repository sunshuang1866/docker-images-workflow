# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, dnf, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: aarch64 构建节点在通过 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 HTTP/2 流错误（Curl error 92: `INTERNAL_ERROR`），dnf 重试所有镜像源后仍无法下载 `guile-2.2.7-6.oe2403sp4.aarch64`，导致构建失败。此错误发生在构建节点的 **aarch64 runner**（`ecs-build-docker-aarch64-04-sp`）上。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile（安装基础编译工具 → 克隆 vvenc 源码 → cmake 构建 → 安装），Dockerfile 内容本身正确无误。失败完全由 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 CDN 在 aarch64 架构上的网络传输不稳定导致，属于 CI 基础设施/上游仓库服务问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。此失败为 `repo.openeuler.org` 仓库的 HTTP/2 流传输瞬时故障（Curl error 92: `INTERNAL_ERROR`），与代码无关。在 CI 中重新触发一次构建（retry）大概率可以成功，因为 RPM 包和 Dockerfile 本身均正确。

### 方向 2（置信度: 低，兜底方案）
如果反复重试仍失败，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=10` 增加下载重试次数，或通过 `echo 'http1_only=1' >> /etc/dnf/dnf.conf` 强制 dnf 回退到 HTTP/1.1 绕过 HTTP/2 流问题。**但此方向仅为网络层的 workaround，根因在上游仓库 CDN 而非 Dockerfile。**

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 HTTP/2 CDN 在 CI 触发时间段是否存在已知的 aarch64 节点服务不稳定问题。
- 确认 aarch64 runner `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络链路是否正常（是否存在中间代理/防火墙干扰 HTTP/2 流）。
- 如果同一 Dockerfile 在 amd64（x86_64） runner 上构建成功，则可进一步佐证问题是 aarch64 仓库/网络专有问题。

## 修复验证要求
无需验证，此为 infra-error，Code Fixer 无需处理代码。
