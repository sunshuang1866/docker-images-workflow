# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在下载 RPM 包时反复出现 HTTP/2 流层协议错误（Curl error 92），`cmake-data` 和 `git-core` 经重试后成功下载，但 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 在两次 HTTP/2 流错误后所有镜像重试耗尽，`dnf install` 最终失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了一个 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）和相关元数据文件，Dockerfile 内容语法正确、依赖声明合理。失败发生在 `dnf` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包阶段，属于 CI 基础设施网络层面的问题——仓库镜像服务端 HTTP/2 连接不稳定，与代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，触发重试即可。** 该失败是 openEuler 24.03-LTS-SP4 仓库镜像在构建时刻的临时性网络波动（HTTP/2 流层错误），与 PR 代码变更无关。Code Fixer 无需处理，直接重新触发 CI 构建流水线，仓库恢复正常后即可通过。

## 需要进一步确认的点
- 如果多次重试后仍然失败，需要确认 openEuler 24.03-LTS-SP4 仓库镜像的可用性状态（`repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/` 是否持续不稳定）。
- 日志中仓库 URL 被脱敏（`repo.****.org`），若需进一步排查需咨询 CI 运维团队获取实际仓库域名。

## 修复验证要求
不适用。该失败为 infra-error，无需代码修改。
