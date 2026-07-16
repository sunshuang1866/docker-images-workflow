# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf, openEuler, SP4, MIRROR, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
ERROR: failed to solve: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`RUN dnf install -y ...`）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像在 CI 构建期间出现 HTTP/2 传输层错误（Curl error 92），多个大型 RPM 包（gcc 34MB、gcc-gfortran 13MB、guile 6.3MB）下载时 HTTP/2 stream 被非正常关闭（INTERNAL_ERROR），dnf 重试耗尽所有镜像后安装失败。两个构建阶段（builder 和 stage-1）均受到相同网络问题影响。

### 与 PR 变更的关联
PR 变更与此次失败**无因果关系**。PR 新增的 Dockerfile 内容正常（与已有的 sp3 版本 Dockerfile 结构一致，仅基础镜像从 `24.03-lts-sp3` 改为 `24.03-lts-sp4`），失败纯粹由 CI 构建时 openEuler SP4 仓库的网络/HTTP 协议层不稳定导致，重试即可恢复。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改，重试 CI 即可。** 这是 openEuler 24.03-LTS-SP4 仓库镜像的临时性 HTTP/2 连接故障，属于基础设施问题。在 dnf 下载大型 RPM 包时，HTTP/2 stream 被服务端非正常关闭（INTERNAL_ERROR），curl 无法完成下载。通常在网络恢复或镜像站负载降低后重跑 CI 即可通过。

## 需要进一步确认的点
- 确认同时间段内其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也遇到相同错误，以排除该仓库镜像的长期可用性问题。
- 若重试后仍然失败，需检查 openEuler 24.03-LTS-SP4 仓库镜像站状态，确认特定 RPM 包（gcc-12.3.1-110、gcc-gfortran-12.3.1-110、guile-2.2.7-6、glibc-devel-2.38-107）在镜像站上是否可正常下载。
