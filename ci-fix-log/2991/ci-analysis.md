# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: SP4仓库HTTP/2下载失败
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install, repo.openeuler.org

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install` 时，从 `repo.openeuler.org` 的 SP4 仓库下载 RPM 包过程中多次遇到 HTTP/2 流错误（Curl error 92），最终 `guile` 包耗尽所有镜像重试次数后下载失败，导致整个 `dnf install` 退出码为 1、Docker 构建失败。

### 与 PR 变更的关联
**与 PR 变更无关**。本次 PR 仅在 `Others/vvenc/` 下新增了一个标准的 Dockerfile（`dnf install -y git gcc gcc-c++ make cmake` + git clone + cmake 构建），该 Dockerfile 本身不存在语法或逻辑错误。失败是因为 openEuler SP4 仓库（`repo.openeuler.org`）在 CI 构建时刻（2026-07-09 14:09 UTC 前后）的 HTTP/2 服务不稳定，向 aarch64 runner 传输大体积 RPM 包（`gcc-c++` 12MB、`guile` 6.3MB）时反复发生 HTTP/2 stream INTERNAL_ERROR，属于纯粹的网络/基础设施故障。日志中 `git-core` 包在第二次重试时下载成功（1513.9 行），但 `guile` 重试耗尽后最终失败，进一步佐证这是间歇性网络问题而非 Dockerfile 缺陷。

## 修复方向

### 方向 1（置信度: 高）
**触发重试**。此为 `infra-error`，Code Fixer 无需修改任何代码。失败根因是 `repo.openeuler.org` 的 HTTP/2 服务端在 aarch64 大文件下载时发生 stream 中断，属于临时性基础设施问题。建议直接重新触发 CI 流水线（re-run），大概率可成功。

## 需要进一步确认的点
- `repo.openeuler.org` 的 SP4 aarch64 仓库在 2026-07-09 前后是否存在已知的 HTTP/2 服务端稳定性问题。
- 如果重试后仍然失败，需检查 dnf 是否可配置禁用 HTTP/2 回退到 HTTP/1.1（如 `dnf install` 前设置 `echo "http2=false" >> /etc/dnf/dnf.conf`），但这属于 Dockerfile 内规避方案，需评估是否引入。
