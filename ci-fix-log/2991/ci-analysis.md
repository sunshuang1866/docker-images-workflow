# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, dnf install, aarch64

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
- 失败原因: 在 aarch64 runner 上执行 `dnf install` 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 HTTP/2 流错误（Curl error 92），其中 git-core 和 gcc-c++ 经重试后成功，guile 耗尽所有镜像重试后失败，导致整个 dnf install 事务回滚，构建中断。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 新增的 Dockerfile 在语法和构建逻辑上完全正确（`dnf install -y git gcc gcc-c++ make cmake` 是标准操作，与其他同类 Dockerfile 一致）。失败是 openEuler 24.03-LTS-SP4 官方仓库 `repo.openeuler.org` 的 HTTP/2 服务端在 aarch64 架构上对特定大文件（如 guile-6.3MB）传输不稳定所致，属于基础设施层面的网络/服务端问题。

需要特别指出：CI 构建运行在 `ecs-build-docker-aarch64-04-sp`（aarch64 节点）上，此次失败仅发生在该架构。若 x86_64 构建也失败且报相同错误，则说明是仓库端的普遍问题；若 x86_64 成功，则问题局限于 aarch64 仓库或网络链路。

## 修复方向

### 方向 1: 重试 CI 构建（置信度: 高）
此类 HTTP/2 流错误通常为仓库服务端的瞬态问题，直接重新触发 CI 构建有很大概率通过。若重试 2-3 次后仍失败，则说明问题非瞬态，需考虑方向 2。

### 方向 2: 强制 dnf/libcurl 使用 HTTP/1.1（置信度: 中）
若问题持续复现，可在 Dockerfile 的 `dnf install` 前添加环境变量或 dnf 配置，强制 libcurl 降级到 HTTP/1.1 协议，绕过 HTTP/2 流层面的不稳定性。此方案需要确认 openEuler 24.03-LTS-SP4 基础镜像中的 libcurl/dnf 版本是否支持该配置。

### 方向 3: 增加 dnf 重试参数（置信度: 低）
配置 dnf 的 `retries` 和 `timeout` 参数（如 `--setopt=retries=10`），增加对单包的下载重试次数，给予镜像重试更多机会。但此方向无法根除 HTTP/2 协议层的不稳定性，仅能提高容错。

## 需要进一步确认的点
1. 该 PR 的 **x86_64 架构 CI job** 是否也失败？若 x86_64 成功，可确认问题仅影响 aarch64 仓库/网络链路。
2. 同期其他使用 openEuler 24.03-LTS-SP4 基础镜像且包含 `dnf install` 的 PR（如 PR #2997、#3101 等）是否报相同错误？若有多例，说明是仓库端系统性问题，需联系 openEuler 基础设施团队排查 repo.openeuler.org 的 HTTP/2 服务端配置。
3. `guile-5:2.2.7-6.oe2403sp4.aarch64.rpm` 文件大小为 6.3MB，而部分成功下载的包（如 gcc 30MB > guile 6.3MB）反而成功，说明问题不一定与文件大小直接关联，可能与特定 CDN 节点或连接复用有关。
