# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf, repo.openeuler.org, aarch64

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 的 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在执行 `dnf install` 安装构建依赖时，`repo.openeuler.org` 仓库服务器出现 HTTP/2 流传输异常（Curl error 92: INTERNAL_ERROR），导致多个 RPM 包（git-core、gcc-c++、guile）下载中断。其中 `git-core` 和 `gcc-c++` 在重试后下载成功，但 `guile`（git 的间接依赖）重试耗尽所有镜像后最终失败，导致整个构建终止。

### 与 PR 变更的关联

**与 PR 变更无关。** 本次 PR 仅新增了一个标准 Dockerfile，其 `dnf install` 命令安装的包（git、gcc、gcc-c++、make、cmake）与其他同类 Dockerfile 完全一致，没有任何异常配置。失败原因是 openEuler 官方软件源 `repo.openeuler.org` 在 CI 构建期间出现 HTTP/2 服务端异常，属于基础设施层面的临时故障。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 这是典型的临时性基础设施故障。错误来自 openEuler 官方 RPM 仓库（`repo.openeuler.org`）的 HTTP/2 服务端流异常，与 PR 代码无关。等待仓库服务恢复后重新触发 CI 构建即可通过。

## 需要进一步确认的点

- 无。日志证据充分，错误模式清晰：HTTP/2 协议层流中断（err 2 = INTERNAL_ERROR）为服务端问题，dnf 自动重试机制已生效，部分包成功恢复，仅 `guile` 耗尽重试次数。此 PR 无需任何代码修改。
