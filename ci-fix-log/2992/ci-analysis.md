# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, MIRROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `RUN dnf install`）
- 失败原因: 从 openEuler 24.03-LTS-SP4 软件仓库下载 RPM 包时，多个包（gcc-gfortran、glibc-devel、guile、gcc）遭遇 HTTP/2 流帧错误（Curl error 92），其中 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 在所有镜像源均尝试失败后导致 dnf 安装命令以退出码 1 终止。

### 与 PR 变更的关联
**与 PR 改动无关。** 本 PR 仅新增了 Multiwfn 的 24.03-lts-sp4 版本 Dockerfile 及其元数据（README.md、image-info.yml、meta.yml）条目。Dockerfile 中 `dnf install` 的软件包列表和语法完全正确，与已有的 sp3 版本 Dockerfile 模式一致。失败是由 openEuler 24.03-LTS-SP4 软件仓库镜像的网络问题（HTTP/2 流层错误）导致的，属于 CI 基础设施问题。

值得注意的是：两个构建阶段（#7 final stage 和 #8 builder stage）同时出现 HTTP/2 流错误，进一步表明这是仓库端的问题而非偶发网络抖动。

## 修复方向

### 方向 1（置信度: 中）
**属于基础设施问题，Code Fixer 无需处理 PR 代码。** 建议：
- 在 CI 非高峰时段重试构建，以确认是否为仓库服务器瞬时负载导致的问题
- 若持续复现，联系 openEuler 仓库基础设施团队排查 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端配置

### 方向 2（置信度: 低）
若希望从 Dockerfile 层面规避此类网络问题，可在 `dnf install` 命令中添加 `--retries=10` 和 `--setopt=timeout=120` 参数以提高网络波动的容错能力。但这不能解决 HTTP/2 协议层面的服务端错误（err 2 = INTERNAL_ERROR）。

## 需要进一步确认的点
1. 确认 openEuler 24.03-LTS-SP4 软件仓库镜像（`repo.****.org`）在构建时间（2026-07-09 14:46 UTC）是否有已知的 HTTP/2 服务中断或降级事件
2. 确认该构建在重新触发后是否能够通过（若通过则确认为瞬时网络问题）
3. 确认 CI 构建环境到 openEuler 24.03-LTS-SP4 仓库的网络链路是否存在 HTTP/2 代理/防火墙干扰
