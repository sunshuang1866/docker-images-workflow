# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2连接失败
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败原因: CI 构建环境中，`dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，多个包（cmake-data、git-core、gcc-c++）遭遇 HTTP/2 协议层 Stream Error（`Curl error (92): Stream error in the HTTP/2 framing layer`）。前两个包通过镜像重试成功下载，但 `gcc-c++-12.3.1-110.oe2403sp4.x86_64` 在多次重试后耗尽所有镜像，导致整个 `dnf install` 命令失败。

### 与 PR 变更的关联
**与 PR 代码无关。** 该 PR 仅新增了一个 GrADS 2.2.3 的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml）。`dnf install` 步骤列出的依赖包与同目录下已有 Dockerfile（`24.03-lts-sp3`）的依赖列表一致，均为合理的编译依赖。失败原因是 openEuler 官方仓库镜像在构建时刻出现 HTTP/2 协议层面的网络波动，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 这是 openEuler 官方仓库镜像的临时性 HTTP/2 协议故障（Curl error 92）。`dnf` 已启用多镜像重试机制（log 中可见 cmake-data 和 git-core 在重试后成功下载），但 gcc-c++ 最终因仓库端持续返回 Stream Error 而落败。Code Fixer 无需处理此问题；建议触发 **CI 重跑（re-run）**，待仓库镜像恢复后构建应自然通过。

### 方向 2（置信度: 低）
如果多次重跑仍失败，可能是 openEuler 24.03-LTS-SP4 仓库对特定网络路径（CI 所在机房到 repo 之间）存在持续的 HTTP/2 兼容性问题。此时可考虑在 Dockerfile 的 `dnf install` 前添加 `echo "http_caching=none" >> /etc/dnf/dnf.conf` 或禁用 HTTP/2 降级到 HTTP/1.1（`echo "setenv = CURL_HTTP_VERSION=1.1" >> /etc/dnf/dnf.conf`），但这属于 CI 环境配置而非 Dockerfile 层面的修复。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在构建时刻是否存在已知的 HTTP/2 服务端问题。
- 确认 CI 环境到该仓库的网络链路是否稳定（是否存在中间代理/防火墙干扰 HTTP/2 帧流）。
- 确认该仓库近期是否有过 CDN 或负载均衡配置变更导致 HTTP/2 流不稳定。
