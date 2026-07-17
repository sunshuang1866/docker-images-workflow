# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2帧错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install

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
- 失败位置: Dockerfile:6（`RUN dnf install -y` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库镜像在下载 `gcc-c++` 包时发生 HTTP/2 帧流错误（Curl error 92），经过多次重试（stream 65、stream 83）后所有镜像均不可用，`dnf install` 以退出码 1 失败。同时 `cmake-data` 和 `git-core` 两个包也遇到了相同的 HTTP/2 帧流错误，但它们最终通过重试成功下载。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 及其元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法正确，依赖包列表合理。失败是由 openEuler 24.03-LTS-SP4 官方仓库镜像的网络层问题（HTTP/2 帧流中断）导致的，属于 CI 基础设施侧的临时性故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。这是 CI 基础设施问题（openEuler 24.03-LTS-SP4 仓库镜像 HTTP/2 连接不稳定），PR 的 Dockerfile 和元数据变更本身没有问题。可以尝试重新触发 CI 构建，等待仓库镜像恢复稳定后构建有望通过。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 问题是否为临时性故障还是持续性问题。如果多次重试 CI 构建仍失败，需要排查 CI runner 到 `repo.****.org` 之间的网络链路是否稳定。
- 需确认同一 CI 环境中，其他使用 24.03-lts-sp4 基础镜像的构建是否也遇到类似问题（如果系统性出现，说明镜像站本身有故障）。
