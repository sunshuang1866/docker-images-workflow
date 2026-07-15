# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, dnf install

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
- 失败原因: `repo.openeuler.org` 的 HTTP/2 服务在 aarch64 构建节点上下载 RPM 包时反复出现 Stream error (Curl error 92)。`git-core` 和 `gcc-c++` 经重试后成功下载，但 `guile` 包耗尽所有 mirror 重试次数后永久失败，导致 `dnf install` 整体退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准的 Dockerfile，内容为 `dnf install -y git gcc gcc-c++ make cmake`，Dockerfile 语法正确、包名有效。失败原因是 `repo.openeuler.org` 仓库服务器端 HTTP/2 协议层面的间歇性故障，属于 CI 基础设施/上游仓库网络问题，非代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**等待上游仓库恢复后重试 CI。** `repo.openeuler.org` 的 HTTP/2 服务存在间歇性 Stream error（Curl error 92: INTERNAL_ERROR），该问题通常由 CDN/反向代理层或源服务器的 HTTP/2 实现缺陷引起，属于临时性基础设施故障。建议隔段时间后重新触发 CI 构建，若仓库服务恢复正常，构建即可通过。Code Fixer 无需修改任何代码。

### 方向 2（置信度: 低）
**若该问题持续复发，可尝试在 Dockerfile 中为 dnf 禁用 HTTP/2 或添加重试。** 例如通过 `dnf` 配置将 `max_parallel_downloads` 降低或通过 `echo 'http2=false' >> /etc/dnf/dnf.conf` 降级到 HTTP/1.1 规避 HTTP/2 流错误。但此方向属于绕过而非修复根因，且可能影响下载速度，仅在基础设施侧长期无法修复时作为临时方案。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 HTTP/2 服务当前健康状态（是否能稳定下载 `guile-2.2.7-6.oe2403sp4.aarch64.rpm`）。
- 确认该 HTTP/2 Stream error 是否仅影响 aarch64 构建节点，还是所有架构均受影响。
- 若其他 PR 同时期也触发 CI 且均失败，则进一步佐证为仓库端基础设施问题。
