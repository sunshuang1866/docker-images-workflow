# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, INTERNAL_ERROR, No more mirrors to try

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
ERROR: failed to solve: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y` 步骤）
- 失败原因: 构建过程中 dnf 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，仓库镜像服务器的 HTTP/2 连接多次被异常中断（`INTERNAL_ERROR`）。`cmake-data` 和 `git-core` 两个包初次下载也遇到同样错误但重试成功；`gcc-c++`（约 13 MB）连续两次遭遇 HTTP/2 流中断，耗尽所有镜像重试后**不可恢复**，导致 dnf 安装步骤整体失败。

### 与 PR 变更的关联
**与 PR 无关。** 该 PR 新增的 Dockerfile 本身语法正确，`dnf install` 命令中列出的所有包名均有效——dnf 成功解析了依赖关系并确认了 258 个待安装包及其 914 MB 的下载清单（`#7 724.4 Dependencies resolved.`）。失败完全由 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库镜像站）的 HTTP/2 服务端连接异常导致，属于 CI 基础设施/网络问题。PR 代码变更无需任何修改。

## 修复方向

### 方向 1（置信度: 高）
这是临时性网络基础设施故障，无需修改代码。等待仓库镜像站 HTTP/2 服务恢复后，**重新触发 CI 构建**即可。此类 `Curl error (92)` HTTP/2 流中断通常为服务器端的短暂性问题（如 CDN 节点异常、反向代理配置问题），与 PR 改动无关。

### 方向 2（置信度: 低）
如果该问题持续反复出现，可在 Dockerfile 中为 dnf 配置重试参数（如 `dnf install --retries 5 --setopt=retries=5`）以提高对间歇性网络波动的容忍度。但此方案治标不治本，根因仍在于仓库镜像站的 HTTP/2 连接稳定性。

## 需要进一步确认的点
- 确认 `repo.****.org` 仓库镜像站在构建时间段（2026-07-13 07:04 UTC 前后）的服务状态，排查是否为 CDN/反代节点的临时故障。
- 如果同样基于 `openeuler:24.03-lts-sp4` 的其他镜像（如模式30/31 中的 Dockerfile）近期也出现类似 `Curl error (92)` 错误，则说明仓库侧问题影响面较大，应上报基础设施运维团队处理。

## 修复验证要求
无。本次失败与 PR 代码无关，不需要 code-fixer 做任何代码修改。重新触发 CI 构建即可验证。
