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
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`:6 (`RUN dnf install -y ...`)
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库镜像服务器在 HTTP/2 协议层发生流错误（Curl error 92），dns 在重试多个镜像后仍无法下载 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 包，导致构建失败。其他两个包（cmake-data、git-core）同样遭遇 HTTP/2 流错误但重试成功，仅 gcc-c++ 重试耗尽所有镜像后失败。

### 与 PR 变更的关联
PR 变更与本次失败**无关**。PR 仅新增了一个标准 Dockerfile，其 `dnf install` 命令语法正确，所列软件包均为 openEuler 24.03-LTS-SP4 仓库中实际存在的包（从日志可见依赖解析成功，列出 258 个包）。失败根因是 openEuler 24.03-LTS-SP4 软件包仓库镜像服务器的 HTTP/2 协议层问题，属于 CI 基础设施故障，非代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
这是一个由 openEuler 24.03-LTS-SP4 软件包仓库镜像稳定性引起的临时性基础设施故障。无需修改 PR 代码：
1. **等待重试**：仓库镜像的 HTTP/2 问题可能是暂时的，等待镜像服务恢复后重新触发 CI 构建即可。
2. **若持续复现**：在 CI 层面对 `dnf` 配置添加重试参数（如 `--retries 10`、降级到 HTTP/1.1 协议），或在 Dockerfile 的 `dnf install` 前配置 yum/dnf 禁用 HTTP/2（`http2=0`）。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）的 HTTP/2 服务是否为已知问题，或是否需要更换镜像源。
- 如果该问题在多次重试后仍持续出现，需确认是否需要降级到 HTTP/1.1 或切换到其他镜像站。

## 修复验证要求
无需修复验证（infra-error，非代码问题）。若后续重试仍然失败，Code Fixer 可考虑在 Dockerfile 中添加 `dnf` 配置以禁用 HTTP/2 或增加重试次数，验证方式为重新触发 CI 构建并确认 `dnf install` 成功完成。
