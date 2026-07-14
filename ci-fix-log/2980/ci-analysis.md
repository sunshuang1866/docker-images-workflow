# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install, gcc-c++

## 根因分析

### 直接错误
```
#7 1776.2 [MIRROR] git-core-2.54.0-2.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/git-core-2.54.0-2.oe2403sp4.x86_64.rpm [HTTP/2 stream 75 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建环境的 openEuler 24.03-LTS-SP4 仓库镜像存在 HTTP/2 连接不稳定问题，`gcc-c++` 包（13MB）经多次重试均因 `Curl error (92): Stream error in the HTTP/2 framing layer` 下载失败。日志显示 `cmake-data` 和 `git-core` 也出现过同样错误但重试后成功，而 `gcc-c++` 两次重试均失败，最终 `dnf` 报告所有镜像均已尝试但无一成功。

### 与 PR 变更的关联
**与 PR 变更无关**。本次 PR 仅新增了一个结构正确的 Dockerfile（参考已有 sp3 版本）及配套元数据文件。`dnf install` 中列出的所有包名均为 openEuler 24.03-LTS-SP4 仓库中的标准包，无拼写错误或不存在的包名。失败纯粹由 CI 构建时仓库镜像服务器的 HTTP/2 协议层不稳定导致，属于基础设施层面的瞬时故障。

## 修复方向

### 方向 1（置信度: 高）
**等待 CI 基础设施恢复后重试**。此失败是 openEuler 24.03-LTS-SP4 软件仓库镜像的 HTTP/2 连接不稳定导致的临时性基础设施问题，与代码变更无关。建议在仓库镜像服务恢复正常后重新触发 CI 构建。若问题持续出现，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=10` 增加重试次数，或临时在 `dnf install` 前切换至更稳定的镜像源。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在 CI 构建时段的可用性状态
- 若其他 PR 的 sp4 构建也同时失败，可确认是仓库侧问题
- 检查是否有 aarch64 架构的构建日志（当前日志仅展示 x86_64 构建），确认是否同样受影响
