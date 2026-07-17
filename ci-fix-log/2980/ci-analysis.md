# CI 失败分析报告

## 基本信息
- PR: #2980 — chore(grads): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
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
```

### 根因定位
- 失败位置: `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y ...` 步骤）
- 失败原因: CI 构建节点（`ecs-build-docker-x86-03-sp`）在通过 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）下载 258 个 RPM 包时，多个包遭遇 HTTP/2 流层内部错误（Curl error 92: `INTERNAL_ERROR`）。`cmake-data` 和 `git-core` 两包在镜像重试后成功下载，但 `gcc-c++`（13 MB）两次重试均失败，最终所有镜像耗尽导致构建失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个 Dockerfile 和对应的文档/元数据文件。Dockerfile 中 `dnf install` 的命令语法正确，包列表完整无遗漏。失败完全由 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 服务端或中间代理在 CI 构建期间的流层协议错误引起，属 CI 基础设施层面的瞬态网络问题。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建。** 该失败为间歇性网络问题（HTTP/2 流错误），`cmake-data` 和 `git-core` 在镜像重试后成功下载，仅 `gcc-c++` 运气不佳。重新触发 CI 大概率可以通过。无需修改任何代码。

### 方向 2（置信度: 低）
**在 `dnf install` 前添加仓库缓存刷新与重试配置。** 若此问题在多轮重试后仍持续出现，可在 Dockerfile 的 `dnf install` 前添加 `dnf makecache --refresh` 或调整 `/etc/dnf/dnf.conf` 中的 `max_retries` 参数增加重试次数。但此改动属于非必要的防御性措施，不建议在首次诊断时就采用。

## 需要进一步确认的点
1. **仓库稳定性**：`repo.****.org`（推测为 `repo.openeuler.org`）的 openEuler 24.03-LTS-SP4 仓库在该 CI 构建时间段（2026-07-13 07:04 UTC）是否存在已知的服务端 HTTP/2 问题或 CDN 节点异常。
2. **CI 节点网络代理**：`ecs-build-docker-x86-03-sp` 节点到仓库之间是否存在 HTTP/2 代理/负载均衡器，其流层实现是否与 curl/DNF 存在兼容性问题。
3. **aarch64 构建结果**：日志仅包含 x86-64 架构构建步骤，需确认 aarch64 架构的构建是否也因同类问题失败，以判断问题是否局限于特定仓库 CDN 节点。
4. **原已存在的 24.03-lts-sp3 镜像**：同仓库内 `grads/2.2.3/24.03-lts-sp3` 使用的是 openEuler 24.03-LTS-SP3 仓库源，其网络可达性是否正常可作为对照参考。
