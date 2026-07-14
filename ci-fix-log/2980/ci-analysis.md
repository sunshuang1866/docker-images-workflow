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
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方软件仓库（`repo.****.org`）在下载多个 RPM 包时持续出现 HTTP/2 流层错误（Curl error 92: Stream error in the HTTP/2 framing layer），其中 `cmake-data` 和 `git-core` 在重试后成功，但 `gcc-c++-12.3.1-110.oe2403sp4.x86_64`（13 MB）在两次 HTTP/2 流错误后耗尽所有镜像重试次数，导致 `dnf install` 失败、Docker 构建中断。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 的改动仅限于：
1. 新增 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile`（纯新增，30 行）
2. 更新 `Others/grads/README.md`（新增一行表格条目）
3. 更新 `Others/grads/doc/image-info.yml`（新增一行表格条目）
4. 更新 `Others/grads/meta.yml`（新增 2 行版本映射）

这些变更均为纯文档/配置性新增，未涉及任何可能影响网络行为的代码。失败发生在 Docker 构建的 `dnf install` 阶段——即从 openEuler 仓库下载依赖包时，这是 CI 基础设施层面的问题（仓库服务端 HTTP/2 流异常），与 PR 代码完全无关。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败是 openEuler 24.03-LTS-SP4 软件仓库的临时性 HTTP/2 服务端问题，表现为间歇性的 `Stream error in the HTTP/2 framing layer`。三个大包（cmake-data、git-core、gcc-c++）中有两个在 dnf 重试后成功下载，说明问题并非持续存在，而是仓库服务在特定时间段的不稳定。等待仓库恢复后重新运行 CI 预计可成功。

### 方向 2（置信度: 中）
**若持续复现，可考虑为 dnf 添加 HTTP/1.1 回退或增加重试次数。** 如果该问题在多次重试后仍然复现，可以在 Dockerfile 的 `dnf install` 前添加配置，将 dnf/repo 的下载协议从 HTTP/2 降级为 HTTP/1.1（如 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置 `~/.curlrc`），或通过 `dnf install --setopt=retries=10 ...` 提高重试次数以容忍间歇性错误。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）是否在 CI 构建时间段（2026-07-13 07:04 UTC 前后）存在已知的服务端 HTTP/2 问题
- 同一时间段其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 PR 构建是否也遇到了相同的 Curl error (92) 失败
- 该仓库镜像是否支持 HTTP/1.1 回退（部分 CDN/反向代理可能仅开放 HTTP/2）

## 修复验证要求
不适用——本失败为 infra-error，无需代码修复。若采用方向 2（添加 HTTP/1.1 回退配置），code-fixer 需在 Dockerfile 修改后触发 CI 构建，确认 `dnf install` 步骤不再出现 Curl error (92) 且所有包正常下载完成。
