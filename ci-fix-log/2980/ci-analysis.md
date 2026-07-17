# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
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
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Dockerfile:6`（`RUN dnf install -y` 步骤）
- 失败原因: CI 构建环境中 dnf 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，多个包（cmake-data、git-core、gcc-c++）遭遇 HTTP/2 流层错误（Curl error 92），其中 gcc-c++ 重试多次后所有镜像均失败，导致 dnf install 整体失败。这是 CI 构建节点与 openEuler 镜像仓库之间的网络基础设施问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了一个标准格式的 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）及对应的元数据文件更新（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法正确、包名存在，失败纯粹是由于 CI 构建节点到 openEuler 镜像仓库的网络不稳定导致的 HTTP/2 流中断，不影响 Dockerfile 本身的正确性。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。这是一次网络基础设施故障（HTTP/2 stream internal error），非代码层面问题。CI 触发重试（retry/re-run）即可。若该问题频繁出现，应由 CI 运维团队排查：
- CI 构建节点与 `repo.****.org` 之间的网络链路质量
- openEuler 镜像仓库端 HTTP/2 服务稳定性
- 是否需要在 dnf 配置中增加 `retries` 或切换下载协议（如强制 HTTP/1.1）

## 需要进一步确认的点
- 无。根因明确，日志证据充分。

## 修复验证要求
不适用（infra-error，无需代码修复）。
