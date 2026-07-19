# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, No more mirrors to try, repo.****.org

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

Docker 构建在 `dnf install` 阶段失败，exit code: 1。Dockerfile 第 6-16 行的 `RUN dnf install -y ...` 步骤中，多个 RPM 包在下载过程中遭遇 openEuler 仓库服务器 HTTP/2 协议流错误（Curl error 92），其中 `cmake-data` 和 `git-core` 在重试后成功，但 `gcc-c++`（13 MB）两次重试均失败，耗尽所有镜像后 dnf 报错退出。

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库（`repo.****.org`）的 HTTP/2 服务端在本次构建期间不稳定，向多个 RPM 包的下载流发送了 `INTERNAL_ERROR` 帧，导致 curl 抛出流错误 (92)。`gcc-c++` 包两次重试均未能在任意镜像上成功下载，dnf 最终失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了一个 Dockerfile 及对应的 README、image-info.yml、meta.yml 条目，这些文件的内容和格式均正确无误。失败原因是 CI 构建时 openEuler 软件源服务器出现了临时性 HTTP/2 协议故障，属于基础设施问题。同一 Dockerfile 在仓库服务器正常时可以通过构建。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码，等待 CI 重试。** 该错误为 openEuler 软件仓库服务器的临时性 HTTP/2 协议故障（服务端向客户端发送了 `INTERNAL_ERROR` 帧），与 PR 代码无关。在仓库服务恢复稳定后，重新触发 CI 构建即可通过。如果该模式频繁出现，可考虑在 Dockerfile 的 `dnf install` 命令前添加仓库重试/换源逻辑（如设置 `max_retries` 或更换镜像站），但这超出了本次 PR 的范围。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在构建时刻是否存在已知的服务端 HTTP/2 稳定性问题。
- 如果连续多次重试 CI 后仍然失败，需要排查仓库源是否对 CI 构建节点（`ecs-build-docker-x86-03-sp`）存在网络连接限制。

## 修复验证要求
无。本次失败为 infra-error，无需修改任何代码，Code Fixer 无需处理。
