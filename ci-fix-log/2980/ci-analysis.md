# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2 镜像站流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境中 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像站（`repo.****.org`）在 HTTP/2 传输层存在不稳定问题，多个 RPM 包（cmake-data、git-core、gcc-c++）下载过程中出现 `Curl error (92): Stream error in the HTTP/2 framing layer`，且 gcc-c++ 包在两次重试后仍然失败，最终因所有镜像源均不可用而构建失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个包含 `dnf install` 命令的 Dockerfile，命令语法和包名均正确无误（日志中 DNF 已成功解析依赖关系并开始下载 258 个包，合计 914MB）。失败纯粹是 CI 基础设施层面 openEuler 24.03-LTS-SP4 仓库镜像站的 HTTP/2 传输不稳定导致的网络错误，非 PR 代码问题。

## 修复方向

### 方向 1（置信度: 高）
**重试触发 CI 流水线。** 该失败是 openEuler 镜像站 HTTP/2 协议的临时性不稳定问题，重试构建大概率可以成功。无需修改任何代码或 Dockerfile。

### 方向 2（置信度: 中）
**在 Dockerfile 中显式禁用 HTTP/2 或切换到 HTTP/1.1。** 如果该镜像站的 HTTP/2 问题长期存在，可考虑在 dnf 配置中禁用 HTTP/2（如设置 `http2=false` 或通过 `--setopt` 调整 curl 选项），但这需要确认 CI 构建环境中的 curl/dnf 支持该配置。

## 需要进一步确认的点
1. 如果多次重试后仍然出现该 HTTP/2 错误，需要联系 openEuler 24.03-LTS-SP4 镜像站运维排查 HTTP/2 协议在 CDN/反向代理层的配置问题。
2. 确认同一时间段内其他使用 openEuler 24.03-lts-sp4 基础镜像的 Dockerfile 构建是否也出现类似错误，以判断是全局基础设施问题还是特定于该 CI runner 的网络问题。
