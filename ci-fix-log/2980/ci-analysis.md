# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2镜像错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在 HTTP/2 传输层出现持续性的 `INTERNAL_ERROR (err 2)` 流错误，导致 `gcc-c++` 等多个包下载失败。DNF 在耗尽重试和所有可用镜像后放弃，构建以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 无关**。PR 新增的 Dockerfile 中 `dnf install` 命令语法正确、包名均真实存在（从日志 `Dependencies resolved` 后的 258 个包列表可确认），构建失败纯粹由 openEuler 官方 RPM 仓库镜像的 HTTP/2 流传输异常引起。`cmake-data`、`git-core`、`gcc-c++` 三个包在不同时间点经历相同的 Curl error (92)，且前两个包在重试后成功下载，表明这是仓库端间歇性 HTTP/2 协议故障，而非 PR 的包名或版本问题。

## 修复方向

### 方向 1（置信度: 高）
**等待基础设施恢复并重试构建**。该失败是 openEuler 24.03-LTS-SP4 仓库镜像服务端的 HTTP/2 传输层间歇性故障，与代码无关。Code Fixer 无需处理 Dockerfile。建议在仓库镜像服务恢复正常后，重新触发 CI 构建。

## 需要进一步确认的点
- 该仓库镜像（`repo.****.org`）的 HTTP/2 协议栈是否存在已知问题或正在维护中，可通过运维团队确认。
- 如果重试后仍然频繁出现相同错误，可考虑在构建前为 DNF 配置添加 `http2=false` 选项强制降级到 HTTP/1.1，规避 HTTP/2 流错误。
