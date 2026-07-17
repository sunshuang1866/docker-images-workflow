# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

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
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像站在 HTTP/2 协议层面出现间歇性流错误（`INTERNAL_ERROR (err 2)`），导致 `gcc-c++` RPM 包在两次重试后仍下载失败。同次构建中 `cmake-data` 和 `git-core` 也遇到相同错误但最终重试成功，说明镜像站当时存在间歇性不稳定，而非包本身不存在。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了一个标准的 GraDS Dockerfile（基础镜像 `openeuler/openeuler:24.03-lts-sp4`）和配套的 README/meta/image-info 元数据更新。Dockerfile 中的 `dnf install` 命令语法正确，包名有效。失败完全由 openEuler 24.03-LTS-SP4 仓库镜像站的网络/协议层瞬时故障导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是仓库镜像站的瞬时网络故障（HTTP/2 流错误），与代码变更无关。最简单有效的处理是等待镜像站恢复后重新运行 CI 流水线。通常此类问题在数小时到一天内自行恢复。

### 方向 2（置信度: 中）
**在 dnf install 命令中添加重试参数。** 如果此类问题频繁出现，可在 Dockerfile 的 `dnf install` 命令中追加 `--setopt=retries=10 --setopt=timeout=120` 等参数增加容错性。但这属于防御性优化而非必须修复，因为根因在服务端。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库镜像站当前是否已恢复正常服务。
- 如果多次重试后仍失败，需要从 CI 节点手动执行 `curl -v` 测试仓库 URL 的可达性和 HTTP/2 兼容性。
- 当前提供的日志仅包含 x86_64 架构的构建失败信息。如果 aarch64 构建也失败（通常 CI 会并行构建双架构），需确认是否为同一原因。
