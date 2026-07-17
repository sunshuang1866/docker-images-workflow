# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

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
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）的 HTTP/2 连接出现流错误（curl error 92: Stream error in the HTTP/2 framing layer），导致 `gcc-c++`、`cmake-data`、`git-core` 三个 RPM 包下载反复失败，最终 `gcc-c++` 在所有镜像重试后仍无法完成下载，`dnf install` 整体失败。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个 Dockerfile 文件及配套的 README、image-info.yml、meta.yml 元数据条目。Dockerfile 中的 `dnf install` 命令语法正确，所列包名均为 openEuler 24.03-LTS-SP4 仓库中存在的有效软件包（日志显示 dnf 已成功解析依赖树并开始下载 258 个包中的前 40 个）。失败是由 CI 构建时 openEuler 仓库镜像的网络问题（HTTP/2 stream error）导致的，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
这是 **infra-error**，无需修改 PR 代码。失败原因是 openEuler 24.03-LTS-SP4 仓库镜像在 CI 构建时出现 HTTP/2 连接异常。应等待仓库镜像恢复正常后**重新触发 CI 构建**（retry）。大多数情况下此类镜像临时故障会自动恢复。

## 需要进一步确认的点
- 确认 `repo.****.org` 仓库镜像的运维状态：是否在构建时间段（2026-07-13 07:04 UTC 左右）存在已知的 HTTP/2 服务中断或网络波动。
- 如果多次 retry 后仍持续出现相同错误，可能需要联系 openEuler 基础设施团队排查仓库镜像的 HTTP/2 配置或负载均衡问题。
- 日志中的其他两个 MIRROR 错误包（`cmake-data`、`git-core`）在重试后成功下载完成，仅 `gcc-c++` 因重试耗尽而失败，进一步说明是间歇性网络问题而非永久性配置错误。
