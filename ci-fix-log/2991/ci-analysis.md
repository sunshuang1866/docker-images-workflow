# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP2协议错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, repo.openeuler.org, No more mirrors to try

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6` (RUN dnf install 步骤)
- 构建节点: `ecs-build-docker-aarch64-04-sp`（aarch64 架构）
- 失败原因: CI 构建过程中，`dnf install` 从 `repo.openeuler.org` 下载 aarch64 RPM 包时，远程服务器的 HTTP/2 连接频繁出现流协议错误 (`Curl error 92: Stream error in the HTTP/2 framing layer`)，多个软件包（`git-core`、`gcc-c++`、`guile`）的下载均受波及。`git-core` 在重试后成功，`gcc-c++` 两次尝试均失败，而 `guile` 耗尽了所有镜像站点重试次数，最终导致整体 `dnf install` 步骤以 exit code: 1 失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`（13 行），其中的 `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 命令与现有 `Others/vvenc/1.14.0/24.03-lts-sp3/Dockerfile` 中同类命令完全一致，属于标准的系统包安装操作。失败完全由 `repo.openeuler.org` 镜像站点的 HTTP/2 协议层故障引起，属于 CI 基础设施问题（服务器端 Curl error 92，HTTP/2 stream INTERNAL_ERROR），非 PR 代码引入。

## 修复方向

### 方向 1（置信度: 高）
**重试即可。** 此失败为 openEuler 官方软件仓库 `repo.openeuler.org` 的间歇性 HTTP/2 协议故障，与 PR 代码无关。重新触发 CI 构建即可——在网络正常时构建应能通过。若问题频繁出现，建议 CI 运维团队排查 openEuler 镜像站的 HTTP/2 stream 稳定性，或考虑在 CI 环境中为 dnf 配置回退镜像源。

## 需要进一步确认的点
- 该 aarch64 构建节点 (`ecs-build-docker-aarch64-04-sp`) 是否持续出现同类问题，还是偶发
- `repo.openeuler.org` 在构建时段是否有已知的服务降级或维护事件
- 是否需要为 CI 的 dnf 配置增加重试次数或 fallback 镜像源以提升容错能力
