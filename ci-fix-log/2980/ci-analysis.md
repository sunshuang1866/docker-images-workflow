# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

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
- 失败原因: CI 构建环境在执行 `dnf install` 下载 RPM 包时，openEuler 24.03-LTS-SP4 的 yum 仓库镜像服务器多次返回 HTTP/2 协议层流错误（`Curl error (92): Stream error in the HTTP/2 framing layer: INTERNAL_ERROR (err 2)`）。其中 `cmake-data` 和 `git-core` 在重试后成功下载，但 `gcc-c++-12.3.1-110.oe2403sp4.x86_64`（13MB）两次下载均失败且已用尽所有可用镜像，导致整个 `dnf install` 步骤退出码 1。

### 与 PR 变更的关联
**与 PR 无关。** PR 的变更仅限于：
1. 新增 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` — Dockerfile 内容正确，`dnf install` 命令语法和包名均无问题
2. README.md、doc/image-info.yml、meta.yml 的元数据更新 — 均为纯文档/配置变更

失败根因是 CI 构建时 openEuler 24.03-LTS-SP4 RPM 仓库镜像的 HTTP/2 服务端问题（服务器端发送 `INTERNAL_ERROR` 导致流异常关闭），属于临时性基础设施故障，与此次 PR 的代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是一个临时性的基础设施故障（CI 网络 / openEuler 24.03-LTS-SP4 RPM 镜像仓库服务端 HTTP/2 问题）。Code Fixer 无需对 Dockerfile 做任何修改。建议触发 CI 重试即可。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的 `Everything` 仓库镜像（`repo.***.org`）在构建时刻是否存在 HTTP/2 服务端已知问题
- 如果同类问题在多 PR 中反复出现，建议在 CI 流程中为 `dnf install` 添加重试机制，或排查仓库镜像的 HTTP/2 配置/代理层稳定性
