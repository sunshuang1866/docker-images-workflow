# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf包源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, dnf install, guile, aarch64

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
- 失败位置: Dockerfile:6 (`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`)
- 失败原因: CI 在 aarch64 runner (`ecs-build-docker-aarch64-04-sp`) 上执行 `dnf install` 时，`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 仓库返回了多次 HTTP/2 流错误（Curl error 92: `INTERNAL_ERROR`），导致多个 RPM 包（`git-core`、`gcc-c++`、`guile`）下载失败。其中 `git-core` 和 `gcc-c++` 在 dnf 重试后恢复，但 `guile` 耗尽所有可用 mirror 后最终失败。

### 与 PR 变更的关联
**与 PR 改动无关**。本次 PR 仅新增了一个正确的 Dockerfile 及配套的元数据/文档更新。Dockerfile 中的 `dnf install` 命令语法和包名均为标准用法。失败完全由 `repo.openeuler.org` 仓库服务器的 HTTP/2 协议层临时故障引起，属于基础设施问题。该问题影响的是 openEuler 24.03-LTS-SP4 的 aarch64 架构仓库。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该失败为 `repo.openeuler.org` 仓库服务器的临时 HTTP/2 协议故障，属于 infra-error。在仓库服务恢复后，重新触发 CI（retry）即可。Code Fixer 无需修改任何代码。

### 方向 2（置信度: 低）
**添加 dnf 重试机制**。如果此类 HTTP/2 流错误频繁发生，可在 Dockerfile 中为 `dnf install` 添加重试逻辑（如 `dnf install -y --setopt=retries=10 git gcc gcc-c++ make cmake`）。但当前错误属于临时基础设施故障，不建议为此增加不必要的重试复杂度。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库在当前时间是否可正常访问
- 如该仓库服务已恢复，直接重新触发 CI 即可验证
- 如相同错误在多次重试后仍出现，需排查 CI runner 到 `repo.openeuler.org` 的网络连通性
