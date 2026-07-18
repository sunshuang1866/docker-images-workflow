# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

## 根因分析

### 直接错误
```
[MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
[MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
[MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
[MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
[FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
Error: Error downloading packages:
  gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境在通过 dnf 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，HTTP/2 连接发生流错误（Curl error 92），多个包（cmake-data、git-core、gcc-c++）的 HTTP/2 stream 未正常关闭。dnf 的镜像重试机制对 cmake-data 和 git-core 重试成功，但 gcc-c++ 两次均失败，最终所有镜像耗尽，构建中断。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 仅新增了一个 Dockerfile（GrADS 2.2.3 on openEuler 24.03-lts-sp4），失败发生在 `dnf install` 依赖包下载阶段，属于 CI 构建节点与 openEuler 仓库之间的 HTTP/2 网络层间歇性故障，代码变更本身不包含任何可能导致此错误的逻辑。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI**。这是典型的网络基础设施间歇性故障（HTTP/2 流中断），与代码逻辑无关。重新触发 CI 构建，大部分情况下网络恢复正常后即可通过。若多次重试仍失败，需排查 openEuler 24.03-LTS-SP4 软件仓库的 CDN/镜像站 HTTP/2 服务稳定性。

## 需要进一步确认的点
- 检查 CI 构建节点（`ecs-build-docker-x86-03-sp`）到 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库）的网络链路是否稳定。
- 若此问题在多天/多次重试后仍持续出现，需联系 openEuler 仓库运维团队排查 HTTP/2 服务的 CDN 配置或服务器端流控制策略。
