# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF 镜像站 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, Error downloading packages

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
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在 HTTP/2 协议层出现流错误——多个 RPM 包（cmake-data、git-core、gcc-c++）在下载过程中因 `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR` 而失败，最终 `gcc-c++` 包耗尽所有重试镜像后仍未成功，导致整个 `dnf install` 命令返回 exit code: 1。

### 与 PR 变更的关联
**与 PR 变更无关**。本次 PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及对应元数据文件（README.md、doc/image-info.yml、meta.yml）。Dockerfile 本身的语法和包名均正确——日志中 `dnf` 成功解析了依赖关系并开始下载 258 个包（总计 914 MB），已有 40 个包下载成功。失败发生在远端 RPM 仓库镜像的 HTTP/2 协议层错误，属于 CI 基础设施/网络层问题，与 PR 代码变更无因果关联。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。这是一个 transient 的 infra-error——openEuler 24.03-LTS-SP4 官方仓库镜像（`repo.****.org`）在构建时点的 HTTP/2 服务存在短暂故障（stream 未正确关闭导致 INTERNAL_ERROR）。大部分 RPM 包已成功下载（40/258），失败由服务端 HTTP/2 协议错误而非代码问题引起。建议重新触发 CI 流水线，等待仓库服务恢复后重试。

### 方向 2（置信度: 低）
如果重试仍然失败，可考虑在 Dockerfile 的 `dnf install` 命令前添加 `echo 'http2=false' >> /etc/dnf/dnf.conf` 以禁用 DNF 的 HTTP/2（降级到 HTTP/1.1），规避该仓库镜像的 HTTP/2 兼容性问题。但此方案为规避措施而非修复根因，需确认仓库镜像的 HTTP/2 问题是否为长期故障后再决定是否应用。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）的 HTTP/2 故障是否已恢复——建议等待一段时间后重新触发构建。
- 确认该仓库是否有计划维护/变更窗口导致 HTTP/2 不稳定。
- 如果重试仍然失败，需要确认禁用 HTTP/2（降级到 HTTP/1.1）是否被项目规范允许。
