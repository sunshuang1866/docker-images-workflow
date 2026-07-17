# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库（`repo.****.org`）在与 CI 构建环境之间的 HTTP/2 通信中反复出现 `INTERNAL_ERROR` 流错误（Curl error 92），导致多个 RPM 包（cmake-data、git-core、gcc-c++）下载失败。`gcc-c++` 包重试耗尽所有镜像后最终失败，`dnf install` 以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个 Dockerfile（`Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`）和配套的文档/元数据文件，Dockerfile 本身语法正确、依赖声明完整。失败原因纯粹是 openEuler 24.03-LTS-SP4 官方 RPM 镜像站在构建时点的网络侧 HTTP/2 协议层故障，相同的 `dnf install` 命令在镜像站恢复后可以正常通过。

## 修复方向

### 方向 1（置信度: 低）
**重新触发 CI 构建。** 由于根因是 RPM 镜像站的临时性 HTTP/2 网络故障，PR 代码本身无问题，等待 openEuler 软件源恢复后重试 CI 即可。此类临时性镜像问题通常不需要修改 Dockerfile。

### 方向 2（置信度: 低）
**在 `dnf install` 中添加重试机制或切换到备选镜像源。** 如果该镜像站的 HTTP/2 问题持续存在，可在 Dockerfile 的 `dnf install` 命令前添加 `dnf config-manager --setopt=retries=10` 增加重试次数，或替换为其他已知稳定的 openEuler 24.03-LTS-SP4 镜像源。但这属于治标不治本的方法，且当前日志已显示 dnf 自行尝试了多轮镜像重试后仍失败。

## 需要进一步确认的点
1. 确认 openEuler 24.03-LTS-SP4 官方 RPM 镜像站（`repo.****.org`）当前是否处于正常状态，是否存在已知的 HTTP/2 协议层问题或 CDN 节点异常。
2. 确认是否只有 x86_64 架构 runner 遇到此问题，还是 aarch64 runner 也有同样问题（日志中仅展示了 x86_64 构建）。
3. 如果问题持续复现，需要确认 CI 构建环境的网络代理/防火墙是否对 HTTP/2 长连接有限制。
