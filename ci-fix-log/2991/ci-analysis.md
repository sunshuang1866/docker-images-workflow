# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP2流传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, aarch64

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 在 aarch64 runner 上执行 `dnf install` 时，从 `repo.openeuler.org` 下载多个 aarch64 RPM 包（git-core、gcc-c++、guile）均遭遇 HTTP/2 流传输错误（Curl error 92），最终 `guile` 包用尽所有重试镜像后下载失败，导致整个 `dnf install` 命令退出码 1。这是 openEuler 24.03-LTS-SP4 aarch64 仓库的临时性基础设施问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 新增了一个标准 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`），其 `dnf install` 命令与仓库中已有的 SP3 版本 Dockerfile 完全一致。失败仅因 CI 构建时 openEuler SP4 aarch64 仓库的 HTTP/2 服务端出现内部错误，多个 RPM 包下载中断。PR 的代码变更本身没有问题，此失败属于 CI 基础设施临时故障。

## 修复方向

### 方向 1（置信度: 低）
**重试 CI 构建**。这是 openEuler 24.03-LTS-SP4 aarch64 仓库 `repo.openeuler.org` 的临时 HTTP/2 服务端问题（`INTERNAL_ERROR`）。等待仓库服务恢复后，重新触发 CI 构建即可通过。如果问题持续出现，CI 运维需排查 `repo.openeuler.org` 的 HTTP/2 配置或 aarch64 仓库节点状态。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在失败时段是否有已知的服务中断或性能问题。
- 如果重新触发 CI 后仍反复出现相同 HTTP/2 流错误，需评估是否应在 Dockerfile 中为 dnf 配置重试策略（如 `dnf install --setopt=retries=10`）或降级为 HTTP/1.1（如 `echo "http2=false" >> /etc/dnf/dnf.conf`）作为兜底方案。
