# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
- 失败原因: 在 aarch64 runner 上执行 `dnf install` 时，`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 仓库在 HTTP/2 下载多个 RPM 包时持续发生流错误（Curl error 92），最终 `guile` 包耗尽所有镜像重试次数后下载失败，导致整个 `dnf install` 命令退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 只做了以下操作：
1. 新增 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`（13 行，标准构建流程）
2. 更新 `README.md`、`doc/image-info.yml`、`meta.yml` 中的元数据条目

Dockerfile 中的 `dnf install -y git gcc gcc-c++ make cmake` 是标准且正确的写法，失败原因是 `repo.openeuler.org` 仓库服务器在 aarch64 架构构建期间出现 HTTP/2 传输层间歇性故障，导致多个包下载被中断，与 PR 代码变更完全无关。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施问题——openEuler 官方仓库 `repo.openeuler.org` 在构建期间出现 HTTP/2 流错误，属于临时的网络/服务端问题。CI 系统管理员应：
- 重新触发 CI 构建（retry），在仓库服务恢复正常后应能通过。
- 如果持续复现，考虑在 CI runner 上配置 dnf 重试策略（如设置 `retries=10` 或 `timeout=300`），或切换到备用镜像源。

### 方向 2（置信度: 低）
如果该问题在多次 retry 后持续出现在 `24.03-lts-sp4` 仓库上，可能需要在 Dockerfile 的 `dnf install` 前增加镜像源切换逻辑（如先尝试华为云镜像站 `repo.huaweicloud.com/openeuler`），但当前证据不支持此方向——日志中 `git-core` 经过重试后成功下载，说明仓库本身是可用的，只是间歇性网络抖动。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段（2026-07-09 14:09 UTC 之后约 28 分钟）是否存在已知的服务降级或 CDN 节点故障。
- 确认同一时段其他 PR 的 aarch64 构建是否也遇到了相同的 HTTP/2 流错误（如为系统性故障，则无需任何 PR 层面的修复）。
- 确认 retry 后是否通过——如果 retry 仍然失败且仅限 SP4 仓库，则需要调查 SP4 仓库镜像节点的健康状况。
