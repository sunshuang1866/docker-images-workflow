# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF 仓库 HTTP/2 流中断
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install, repo.openeuler.org, aarch64

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install` 时，从 `repo.openeuler.org` 下载 RPM 包过程中遭遇 HTTP/2 流层错误（Curl error 92：HTTP/2 stream was not closed cleanly: INTERNAL_ERROR），多个包（`git-core`、`gcc-c++`、`guile`）均受影响。其中 `guile`（git 的依赖包）在重试耗尽所有镜像后下载失败，导致整个 `dnf install` 命令退出码 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准的 vvenc Dockerfile（包含 `dnf install -y git gcc gcc-c++ make cmake` 命令）及配套的 README、image-info.yml、meta.yml 更新。失败根因是 `repo.openeuler.org` 在 aarch64 架构下提供 HTTP/2 服务时发生流层传输中断，属于 CI 基础设施 / 软件源服务器端的网络问题，Dockerfile 本身不存在任何语法或逻辑错误。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施 / 网络问题，无需修改代码。** 这是 `repo.openeuler.org` 镜像站在 aarch64 构架上的 HTTP/2 服务临时不稳定性导致的下载失败。建议：
- 触发 CI 重试（re-run），网络波动类问题大概率在重试后消失。
- 若持续复现，联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 服务端配置或 CDN 节点状态。

## 需要进一步确认的点
- `repo.openeuler.org` 在 aarch64 架构上的 HTTP/2 服务是否存在已知的稳定性问题或限流策略。
- 检查同一时段其他使用 `repo.openeuler.org` 且目标为 aarch64 的 PR CI 构建是否也有类似失败，以判断是否为单点 runner 网络问题还是镜像站全局问题。
