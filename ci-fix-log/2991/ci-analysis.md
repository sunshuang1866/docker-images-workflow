# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: Dockerfile:6 — `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`
- 失败原因: CI 在 aarch64 runner 上构建时，`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 软件仓库在 HTTP/2 传输中多次出现 `INTERNAL_ERROR`（Curl error 92），导致多个 aarch64 RPM 包（`git-core`、`gcc-c++`、`guile`）下载失败。其中 `git-core` 重试后成功，`gcc-c++` 两次重试均失败，`guile` 在耗尽所有镜像重试后最终导致 dnf 安装失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 vvenc Dockerfile 内容正确，`dnf install -y git gcc gcc-c++ make cmake` 是标准操作。失败根因是 openEuler 软件仓库（`repo.openeuler.org`）的 HTTP/2 服务端问题，属于 CI 基础设施/网络层面故障，任何在该时刻尝试从该仓库下载 aarch64 包的构建都会遇到同样问题。

## 修复方向

### 方向 1（置信度: 低）
**重试构建。** HTTP/2 流错误（INTERNAL_ERROR）通常是临时的服务端/CDN 问题，重新触发 CI 构建有较大概率通过。Code Fixer 无需修改任何代码。

### 方向 2（置信度: 低）
**配置 dnf 回退到 HTTP/1.1。** 如果问题持续出现，可在 Dockerfile 的 `dnf install` 前配置 dnf/libcurl 禁用 HTTP/2（如设置 `http2=false` 或通过环境变量），绕过 HTTP/2 流错误。但这属于服务端问题的工作绕过（workaround），不应作为长期修复方案。

## 需要进一步确认的点
1. 该仓库的 x86_64 构建（trigger 层）是否成功？日志中仅显示 aarch64 runner 的构建失败，需确认 x86_64 侧的状态以判断是否为 aarch64 仓库独有问题。
2. `repo.openeuler.org` 的 HTTP/2 服务是否存在已知问题？建议联系 openEuler 基础设施团队确认 CDN/仓库服务状态。
3. 观察近期其他 PR（特别是同样使用 `24.03-lts-sp4` + aarch64 的构建）是否也出现类似的 HTTP/2 流错误，以判断是否为该仓库的持续性故障。
