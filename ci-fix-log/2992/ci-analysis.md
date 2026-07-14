# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), dnf download, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库的多个镜像站持续返回 HTTP/2 流错误（Curl error 92），导致 dnf 在下载 gcc、gcc-gfortran、glibc-devel、guile 等 RPM 包时反复失败。最终 gcc 包耗尽所有备用镜像后彻底失败，拉取 157 个包中的一个关键包无法完成。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个结构正确的 Dockerfile（与已有 sp3 版本的模式一致），失败完全由外部 openEuler SP4 软件仓库的 HTTP/2 基础设施不稳定引起。运行阶段（#7，32 个包）中的部分包通过重试最终下载成功，但构建阶段（#8，157 个包）中的 gcc 包在尝试所有镜像后仍未成功，说明问题具有间歇性但不影响所有包的稳定下载。

## 修复方向

### 方向 1（置信度: 中）
**无需修改 PR 代码**，这是基础设施故障。CI 运维人员应排查 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 代理/负载均衡配置，确认是否有节点或反向代理存在 HTTP/2 流中断问题。可在问题修复后重新触发 CI 构建（retry）。

### 方向 2（置信度: 低）
若仓库基础设施短期内无法修复，可在 Dockerfile 的 dnf 命令前增加重试逻辑（如 `dnf install --setopt=retries=10 ...`），或在 dnf 配置中降级到 HTTP/1.1（`dnf --setopt=minrate=0 --setopt=timeout=300`），提高对间歇性 HTTP/2 错误的容忍度。但这只是绕过方案，不应作为永久修复。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 软件仓库在该 CI 运行时间点（2026-07-09 14:46）是否存在已知的 HTTP/2 协议或镜像站故障
- 同一时间段内，其他使用 `openeuler/openeuler:24.03-lts-sp4` 基础镜像的 PR 是否也遇到类似错误，以确认影响范围是否为全局性
- CI runner（`ecs-build-docker-x86-03-sp`）到 openEuler 仓库镜像的网络链路是否存在限流或丢包
