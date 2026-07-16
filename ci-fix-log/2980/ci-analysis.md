# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库 HTTP/2 流错误
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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的软件包仓库镜像（`repo.****.org`）在通过 HTTP/2 协议传输 RPM 包时频繁出现流错误（Curl error 92），导致 `gcc-c++` 等大型包下载失败，dnf 重试耗尽所有镜像后构建终止。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增了一个正确的 GrADS 2.2.3 在 openEuler 24.03-LTS-SP4 上的 Dockerfile，Dockerfile 语法和包列表均无问题。失败完全由 CI 构建环境中 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 网络传输层不稳定导致。日志中可见 `cmake-data` 和 `git-core` 同样触发了 Curl error 92，经 dnf 自动重试后成功下载，但 `gcc-c++`（13 MB）的两次重试均失败，最终耗尽所有镜像。

## 修复方向

### 方向 1（置信度: 低）
**重试构建**。HTTP/2 流错误（Curl error 92 / INTERNAL_ERROR）通常是网络中间设备或镜像站点的瞬时问题，与代码无关。等待仓库网络恢复稳定后重新触发 CI 构建，大概率可以成功。注意：日志中 `cmake-data` 和 `git-core` 在报错后被 dnf 成功重试下载，说明网络并非完全不通而是间歇性异常。

### 方向 2（置信度: 低）
**关闭 dnf 的 HTTP/2 回退到 HTTP/1.1**。如果该镜像仓库的 HTTP/2 实现持续不稳定，可在 Dockerfile 的 `dnf install` 之前通过 dnf 配置或 libcurl 环境变量禁用 HTTP/2（如设置 `http2=0` 或通过 `--setopt` 调整）。但这属于绕过基础设施缺陷的变通方案，首选应是方向 1。

## 需要进一步确认的点
1. 该 openEuler 24.03-LTS-SP4 镜像仓库（`repo.****.org`）是否存在已知的 HTTP/2 协议兼容性问题，建议与仓库运维团队确认。
2. 同样的 Dockerfile 在其他架构（aarch64）或同仓库不同 SP 版本（如 SP3）是否也触发相同错误——如果其他架构/版本正常，则进一步证实是该 SP4 仓库的独立问题。
3. 在非 CI 环境中手动执行 `dnf install` 相同包列表，验证是否为 CI 网络环境特有的代理/防火墙对 HTTP/2 流的干扰。
