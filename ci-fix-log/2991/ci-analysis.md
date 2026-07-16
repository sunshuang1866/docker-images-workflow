# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, repo.openeuler.org, aarch64, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install` 时，从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 aarch64 RPM 包（git-core、gcc-c++、guile）时反复出现 HTTP/2 流错误（Curl error 92），git-core 重试后成功，但 guile 包的下载耗尽所有 mirror 重试后仍失败，导致整个 `dnf install` 步骤以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 新增的 Dockerfile 内容完全正确——`dnf install -y git gcc gcc-c++ make cmake` 是合法的包安装命令，vvenc 1.14.0 在 GitHub 上确实存在 `v1.14.0` tag。失败纯粹是因为 `repo.openeuler.org` 的 aarch64/SP4 仓库在构建时出现了 HTTP/2 协议层面的传输错误，属于 CI 基础设施/上游镜像站问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该失败为上游镜像站 `repo.openeuler.org` 的临时 HTTP/2 传输问题，与 PR 代码无关。多数情况下重新触发 CI 流水线即可通过（RPM 包下载的网络波动通常是临时的）。若持续失败，需排查 `repo.openeuler.org` 对 aarch64 构建节点（位于 `ecs-build-docker-aarch64-04-sp`）的网络可达性和 HTTP/2 兼容性。

## 需要进一步确认的点
- `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在当前时段是否存在持续的 HTTP/2 服务端问题。可手动在 aarch64 构建节点上使用 `curl --http2` 测试以下 URL 是否稳定可下载：
  - `https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm`
  - `https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm`
- 若 x86_64 构建在该 PR 上通过而 aarch64 失败，则说明问题是 aarch64 仓库特异性或特定节点的网络问题。
