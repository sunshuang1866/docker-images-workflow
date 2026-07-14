# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
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
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 RPM 仓库镜像在服务 `gcc-c++` 等软件包下载时出现间歇性 HTTP/2 协议流错误（Curl error 92），DNF 在多次重试后耗尽所有镜像源，导致包下载失败。

### 与 PR 变更的关联
**与 PR 代码变更无关**。该 PR 新增了一个 Dockerfile 文件，其 `dnf install` 命令语法和包名均正确。失败是由于 openEuler 24.03-LTS-SP4 官方 RPM 仓库的 CDN/镜像节点在提供服务时发生了 HTTP/2 协议层面的传输错误。日志中可见 `cmake-data` 和 `git-core` 的下载也遇到了同样的 HTTP/2 流错误，但通过换镜像重试成功恢复；`gcc-c++` 在两次重试失败后耗尽所有可用镜像，最终导致构建失败。

## 修复方向

### 方向 1（置信度: 高）
这是 **CI 基础设施 / 上游镜像站问题**，Code Fixer 无需处理。应该：
1. 等待 openEuler 24.03-LTS-SP4 RPM 仓库镜像恢复稳定后，重新触发 CI 构建（`retest`）。
2. 若问题持续出现，联系 openEuler 基础设施团队排查 `repo.****.org` 的 HTTP/2 服务配置或 CDN 节点健康状态。

## 需要进一步确认的点
- 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 软件源）当前是否在维护或存在已知的 HTTP/2 服务故障。
- 确认其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否出现同样的 Curl error (92) 错误，以判断是否为全局性问题。
