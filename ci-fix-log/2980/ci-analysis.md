# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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
- 失败原因: CI 构建环境在通过 dnf 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，多个包（`cmake-data`、`git-core`、`gcc-c++`）遭遇 HTTP/2 流错误（Curl error 92）。`gcc-c++` 包在重试所有可用镜像后仍下载失败，导致整个 `dnf install` 命令退出码为 1。

### 与 PR 变更的关联
**与 PR 无关。** PR 变更仅为新增 GraDS 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法正确，所列包名均为 openEuler 24.03-LTS-SP4 仓库中存在的合法包名。失败完全由 openEuler 包仓库镜像的网络层 HTTP/2 协议中断引起，属于 CI 基础设施/网络层面的瞬态故障。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 此为 CI 基础设施问题（openEuler 24.03-LTS-SP4 仓库镜像 HTTP/2 服务不稳定），建议重试 CI 构建。待镜像仓库服务恢复正常后，同一 Dockerfile 可正常通过构建。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 的 `repo.****.org` 仓库镜像在构建时段的可用性状态。若该镜像站持续不稳定，可考虑在 Dockerfile 中切换为其他可用的 openEuler 镜像源（如 `repo.openeuler.org`），或为 dnf 配置添加 `retries=10` 及更长的超时时间以增加容错性。
