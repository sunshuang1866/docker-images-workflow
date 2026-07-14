# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, MIRROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1845.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 65 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 83 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1970.5 [FAILED] gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1970.5 Error: Error downloading packages:
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件源镜像站在下载 `gcc-c++` RPM 包时反复出现 HTTP/2 流错误（Curl error 92），所有镜像重试均失败，导致 dnf 安装中断，构建退出。

### 与 PR 变更的关联
**无关。** PR 新增了一个完整的 Dockerfile，其 `dnf install` 安装的包列表（gcc、cmake、autoconf 等）均为 openEuler 24.03-LTS-SP4 官方仓库中的标准包。同一构建过程中其他包（如 `cmake-data`、`git-core`）也曾出现同类 HTTP/2 流错误后重试成功，表明问题出在软件源镜像的网络稳定性上，而非 PR 的包列表或语法有误。这是一个 CI 基础设施层面的瞬时故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重新触发 CI 构建即可。** 这是软件源镜像站 HTTP/2 连接瞬时不稳定导致的下游下载失败，属于基础设施故障。待镜像站恢复稳定后重跑 CI 大概率通过。如果同一构建多次重试均失败，则需排查 repo 镜像站对 HTTP/2 协议的支持稳定性。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像站（`repo.****.org`）在该时间段是否有网络抖动或 HTTP/2 服务故障。
- 如果重试多次后仍然失败，需检查 CI 构建节点到 openEuler 24.03-LTS-SP4 仓库的网络连通性和 HTTP/2 兼容性。
