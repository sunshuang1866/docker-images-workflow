# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流中断
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`:6-16（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像（`repo.****.org`）在处理 HTTP/2 请求时，对部分大型 RPM 包（`cmake-data`、`git-core`、`gcc-c++`）返回 HTTP/2 `INTERNAL_ERROR` 帧，导致下载流被中断。`cmake-data` 和 `git-core` 在重试后成功，但 `gcc-c++`（13 MB）连续两次 HTTP/2 流错误后耗尽所有镜像重试机会，`dnf` 安装失败。

### 与 PR 变更的关联
PR 新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`，其中 `dnf install` 命令本身语法正确，所需包名均有效（总共 258 个包被正确解析并开始下载）。失败由 **openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 协议层问题** 导致，与 PR 的代码变更无关。该 Dockerfile 在仓库镜像正常工作时应能通过构建。

## 修复方向

### 方向 1（置信度: 中）
**等待仓库镜像恢复后重试**。错误为服务器端 HTTP/2 协议问题（`INTERNAL_ERROR`），属于 transient infra-error。可在 CI 中重新触发构建（retry），若仓库镜像 HTTP/2 问题已自愈则构建通过。

### 方向 2（置信度: 低）
若该仓库镜像的 HTTP/2 问题反复出现，可在 Dockerfile 的 `dnf install` 前禁用 HTTP/2，强制使用 HTTP/1.1 下载 RPM 包。例如在 `dnf install` 前设置环境变量或通过 dnf 配置禁用 HTTP/2（`echo "http2=false" >> /etc/dnf/dnf.conf`）。但此方案为被动规避，无法解决镜像站的根本问题，且可能影响下载性能。

## 需要进一步确认的点
1. `repo.****.org` 的实际域名和其 HTTP/2 服务端实现（如 nginx/CDN 版本），确认 HTTP/2 INTERNAL_ERROR 是否为已知 bug
2. 其他基于 openEuler 24.03-LTS-SP4 的 Dockerfile 构建是否也遇到相同错误（判断是全局问题还是偶发）
3. 仓库镜像是否有已知的 HTTP/2 限流策略，CI 环境的大规模并发下载是否触发了服务端流控
4. 在 aarch64 runner 上是否也会遇到同样的 HTTP/2 错误（日志仅为 x86_64 runner 的构建过程）
