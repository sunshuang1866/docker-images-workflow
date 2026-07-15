# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR, MIRROR, No more mirrors to try

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 镜像仓库（`repo.****.org`）在通过 HTTP/2 协议提供 RPM 包下载时发生传输层流错误（Curl error 92），导致 `gcc-c++` 包的两次下载尝试均失败，最终 `dnf install` 因所有镜像均已尝试无果而退出。受影响的包还包括 `cmake-data`（1 次失败后重试成功）和 `git-core`（1 次失败后重试成功）。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增的 Dockerfile 语法正确、包名有效（从日志可见大部分包下载成功，安装列表中的 package list 被正确解析）。失败原因是 openEuler 24.03-LTS-SP4 官方 YUM 仓库在 CI 构建期间的 HTTP/2 传输层不稳定，属于基础设施层面的网络问题。Dockerfile 本身无需修改。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该错误是仓库镜像端 HTTP/2 传输层临时故障，与代码无关。等待仓库镜像恢复后重新运行 CI 流水线即可，Dockerfile 无需任何修改。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在 CI 构建时段是否有已知的 HTTP/2 服务端异常或维护窗口。
- 如果重试后仍然失败，需要排查 CI runner 所在网络环境到仓库的 HTTP/2 连接是否被中间代理或防火墙干扰。
