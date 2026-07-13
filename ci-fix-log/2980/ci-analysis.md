# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
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
#7 1970.5   gcc-c++-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6-16`（`RUN dnf install` 步骤）
- 失败原因: CI 构建环境中，openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在 HTTP/2 下载过程中发生多次流中断（`INTERNAL_ERROR (err 2)`），导致 13MB 大小的 `gcc-c++-12.3.1-110.oe2403sp4.x86_64.rpm` 包多次下载失败，最终 `dnf` 报告所有镜像均已尝试但无法完成下载，构建退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 新增的 Dockerfile 语法正确、包名正确，`dnf install` 命令本身无问题。失败根因是 CI 构建节点与 openEuler 24.03-LTS-SP4 仓库镜像之间的网络层 HTTP/2 协议会话异常。日志中可见三个镜像同时出现问题（`cmake-data`、`git-core`、`gcc-c++`），其中前两个在重试后成功，`gcc-c++` 因文件较大（13MB）多次重试均被流中断。

## 修复方向

### 方向 1（置信度: 高）
**重试即可。** 该错误为临时性网络/镜像站问题，不是 Dockerfile 编码错误。建议在 CI 中重新触发本次构建；若多次重试持续失败，需联系 openEuler 基础设施团队排查 24.03-LTS-SP4 仓库镜像站的 HTTP/2 配置或负载均衡器状态。

### 方向 2（置信度: 低）
若镜像站问题持续存在，可考虑在 Dockerfile 的 `dnf install` 前添加 dnf 配置以降低并发连接或禁用 HTTP/2（如设置 `max_parallel_downloads=1` 或 `http2=false`），但这只是规避手段，不解决根本原因。

## 需要进一步确认的点
1. **镜像站状态**: 需确认 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在该时间段是否存在已知的 HTTP/2 服务中断或限流。
2. **CI 节点网络**: 确认 `ecs-build-docker-x86-03-sp` 构建节点到镜像站的网络链路是否稳定，是否存在代理/防火墙干扰 HTTP/2 流。
3. **重试结果**: 连续多次触发构建是否能稳定复现此问题，若不能则确认是偶发网络抖动。
