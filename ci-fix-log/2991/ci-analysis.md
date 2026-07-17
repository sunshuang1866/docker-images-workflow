# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP2传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, repo.openeuler.org, aarch64

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: CI 的 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在通过 dnf 从 `repo.openeuler.org` 下载 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 HTTP/2 传输层错误（Curl error 92: Stream error in the HTTP/2 framing layer），其中 git-core 和 gcc-c++ 通过镜像重试成功下载，但 `guile-5:2.2.7-6.oe2403sp4.aarch64` 在所有镜像重试后仍失败，导致整个 dnf install 步骤退出码 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准 Dockerfile（安装系统依赖、克隆上游仓库、cmake 构建），Dockerfile 中的 `dnf install` 命令语法和包名均正确。失败根因是 `repo.openeuler.org` 仓库在 aarch64 架构上的 HTTP/2 传输问题，属于 CI 基础设施/网络层面的临时故障。重试 CI 构建有较大概率通过。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，触发 CI 重试即可。** 该失败是 openEuler 官方仓库 `repo.openeuler.org` 在构建时段的 HTTP/2 传输层临时故障，与 PR 的 Dockerfile 或任何代码变更无关。在 Jenkins 中重新触发该 job 即可。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 是否在构建时段存在已知的服务端 HTTP/2 问题或 CDN 节点故障。
- 如果多次重试仍然失败，需检查 CI runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否存在持续性问题，必要时可将 dnf 源切换到其他镜像站（如 `mirrors.tuna.tsinghua.edu.cn` 等）。
