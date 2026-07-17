# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf download

## 根因分析

### 直接错误
```
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`RUN dnf install` 步骤，builder 阶段）
- 失败原因: CI 构建环境与 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）之间的 HTTP/2 连接不稳定，多个 RPM 包下载过程中出现 `Curl error (92): Stream error in the HTTP/2 framing layer`，最终 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 耗尽所有镜像重试后下载失败，导致 `dnf install` 返回 exit code 1。

全貌：日志中共出现 5 次 HTTP/2 流错误，涉及 `gcc-gfortran`（3 次）、`glibc-devel`（1 次）、`guile`（1 次）、`gcc`（1 次，致命）。其中 stage-1（#7，32 个包）和 builder 阶段（#8，157 个包）均受波及，说明网络问题具有系统性和持续性，而非针对特定 RPM 包的偶发故障。

### 与 PR 变更的关联
**与 PR 代码变更无直接因果关系。** PR 仅新增了一个标准格式的 Dockerfile（含常规 `dnf install`），未引入任何可能导致网络错误的代码。该 Dockerfile 引用的基础镜像为 `openeuler/openeuler:24.03-lts-sp4`，其 dnf 仓库配置指向 openEuler 24.03-LTS-SP4 仓库，该仓库在 CI 构建时段出现 HTTP/2 流层间歇性中断。这是基础设施侧的网络/服务端问题，不是 PR 改动触发的代码缺陷。PR 代码本身不存在语法或逻辑错误。

## 修复方向

### 方向 1（置信度: 中）
**基础设施问题，无需代码修复。** 等待 openEuler 24.03-LTS-SP4 仓库服务恢复稳定后重试 CI。HTTP/2 流帧错误（`INTERNAL_ERROR (err 2)`）通常指向服务端 HTTP/2 实现缺陷或中间代理/负载均衡器的协议处理异常，非客户端可控。建议：
- 等待一段时间后触发 CI 重新构建
- 若持续失败，联系 openEuler 24.03-LTS-SP4 仓库维护方排查 HTTP/2 服务端问题

### 方向 2（置信度: 低）
如果仓库侧问题短期内无法修复，可尝试在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager` 步骤，将 `repo.****.org` 的 `http2` 选项关闭，强制 dnf/curl 回退到 HTTP/1.1 协议以绕过 HTTP/2 流错误。但这属于绕过方案而非根因修复。

## 需要进一步确认的点
- 该仓库（`repo.****.org`）是否在 CI 环境中频繁出现 HTTP/2 流错误，还是此次为孤立事件？需要查看同一时段其他 PR 的构建历史以确认。
- openEuler 24.03-LTS-SP3 仓库（现有 multwfn Dockerfile 所依赖的仓库）在同一 CI 环境中是否也出现类似 HTTP/2 错误？若 sp3 正常而 sp4 异常，问题更可能出在 sp4 仓库的服务端配置。
- CI runner 所在网络环境与 `repo.****.org` 之间是否存在中间代理或 CDN 层，该层是否对 HTTP/2 长连接有超时或重置策略。
