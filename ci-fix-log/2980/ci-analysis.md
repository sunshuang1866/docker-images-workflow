# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, All mirrors were already tried without success

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
- 失败原因: openEuler 24.03-LTS-SP4 官方镜像站在构建期间出现 HTTP/2 传输层流错误（`curl error 92: Stream error in the HTTP/2 framing layer`），导致 `gcc-c++` 等 RPM 包下载失败，dnf 重试所有镜像后仍无法下载，整个构建中止。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 的唯一代码变更是在 Dockerfile 中通过 `dnf install` 安装 30 个依赖包。Dockerfile 本身的语法和包名均为正确，DNS 解析正常（镜像站元数据获取成功），安装事务解析通过（258 个包已列出摘要）。失败完全由 openEuler 镜像站的 HTTP/2 反向代理/负载均衡在特定时段不稳定导致，属于 CI 基础设施侧的偶发网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，触发重试即可。** 该失败属于 CI 基础设施问题（镜像站 HTTP/2 连接不稳定），Dockerfile 本身没有问题。建议等待镜像站恢复后重新触发 CI 构建（retry / re-run）。通常此类问题会在数小时到 1 天内自行恢复。

### 方向 2（置信度: 中）
若该问题频繁复现，可考虑在 `dnf install` 命令前添加重试逻辑（如 `dnf install --retries 5` 或 wrapp shell retry loop），提高网络波动的容错能力。但通常此类 HTTP/2 流错误为偶发，不应作为必要条件。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 镜像站（`repo.****.org`）在构建时间点前后的可用性状态，是否为计划维护或波动。
- 重新触发 CI 构建后确认是否仍出现相同错误，如持续失败则可能需要排查是否镜像站对构建节点 IP 存在连接限制。

## 修复验证要求
无需修复，仅需重试 CI。
