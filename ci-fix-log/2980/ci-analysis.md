# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1199.1 [MIRROR] cmake-data-3.31.12-1.oe2403sp4.noarch.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/cmake-data-3.31.12-1.oe2403sp4.noarch.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建环境在 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，多次遭遇 HTTP/2 流层协议错误（`Curl error (92): Stream error in the HTTP/2 framing layer`, `INTERNAL_ERROR (err 2)`）。受影响包包括 `cmake-data`、`git-core`、`gcc-c++`，其中 `gcc-c++`（13 MB）因重试耗尽所有镜像而最终失败（`No more mirrors to try`），导致 `dnf` 退出码 1，Docker 构建中止。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 仅新增了一个标准格式的 Dockerfile 和相应的文档/元数据条目，不涉及任何代码逻辑问题。失败完全是 openEuler 24.03-LTS-SP4 仓库镜像服务端的 HTTP/2 传输层临时故障所致，属于 CI 基础设施层面的网络波动。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 openEuler 24.03-LTS-SP4 仓库镜像的临时性 HTTP/2 协议层故障，与 Dockerfile 内容无关。建议重新触发 CI 构建（retry），待仓库镜像服务恢复后即可通过。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org/openEuler-24.03-LTS-SP4/`）的 HTTP/2 服务是否存在已知问题或正在维护中。
- 如果多次 retry 后仍然出现相同错误，考虑在 CI 构建脚本或 Dockerfile 中将 `dnf` 配置为使用 HTTP/1.1 协议（绕过 HTTP/2 问题），或切换到其他可用的镜像站。
