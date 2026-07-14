# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM 源 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件源（`repo.****.org`）在 Docker 构建期间出现 HTTP/2 传输层错误（Curl error 92），多个 RPM 包（cmake-data、git-core、gcc-c++）下载时 HTTP/2 流异常中断。其中 `gcc-c++` 包经多次重试仍失败，DNF 耗尽所有镜像源后报错退出。

### 与 PR 变更的关联
**无关。** 该 PR 仅新增了一个标准的 GrADS Dockerfile，其 `dnf install` 命令中列出的全部是 openEuler 24.03-LTS-SP4 官方仓库中的常规软件包，Dockerfile 本身不存在语法错误、包名拼写错误或依赖缺失。失败完全由 CI 构建时 RPM 软件源发生 HTTP/2 传输故障所致，属于 CI 基础设施临时性问题。

## 修复方向

### 方向 1（置信度: 高）
等待 CI 基础设施恢复后重新触发构建。该失败是 openEuler 官方 RPM 软件源（`repo.****.org`）的 HTTP/2 传输层临时故障，与 PR 代码变更无关。通常此类问题在数小时至一天内由镜像站运维方自行恢复。直接 retrigger CI 即可验证。

## 需要进一步确认的点
- 确认 `repo.****.org` 的 openEuler 24.03-LTS-SP4 软件源当前是否已恢复正常（可在构建节点上手动 `curl` 测试目标 RPM 包可达性）。
- 如果多次 retrigger 均在同一软件源上失败，可考虑在 Dockerfile 中切换到备用镜像源或调整 DNF 的 HTTP/2 相关配置（如禁用 HTTP/2）。
