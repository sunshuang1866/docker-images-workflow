# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, [MIRROR], No more mirrors to try

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`dnf install` 步骤，builder 阶段 `#8`）
- 失败原因: openEuler 24.03-LTS-SP4 软件源镜像服务器在 CI 构建期间出现 HTTP/2 流传输故障（Curl error 92: `INTERNAL_ERROR`），多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载时 HTTP/2 连接被不正常关闭。`gcc` 包在重试所有镜像后均失败，导致 dnf 整体报错退出。

### 与 PR 变更的关联

**与 PR 代码变更无关。** PR 仅新增了 multiwfn SP4 的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `dnf install` 命令语法正确，所需包名有效（依赖解析阶段正常通过，问题仅发生在下载阶段）。根因是 openEuler 24.03-LTS-SP4 软件源的 CDN/镜像基础设施在构建时段的 HTTP/2 连接异常。

同步观察：运行时阶段 `#7`（`stage-1`）的 dnf install 在并行下载过程中也遭遇了相同的 HTTP/2 流错误（`glibc-devel`、`gcc-gfortran`），虽有个别包重试成功，但最终因 builder 阶段 `#8` 失败而被整体取消（`CANCELED`）。两个独立阶段的并行下载都触发了同一错误，进一步排除了 Dockerfile 本身的问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败属于 openEuler 软件源基础设施的临时性故障（HTTP/2 连接异常），与 PR 代码变更无关。等待软件源恢复后重新运行 CI 即可通过。如果持续复现，需要联系 openEuler 基础设施团队排查 repo 服务器的 HTTP/2 配置或 CDN 节点状态。

### 方向 2（置信度: 低）
如果反复重试均失败，可考虑在 Dockerfile 的 `dnf install` 前增加重试逻辑或强制 dnf 使用 HTTP/1.1（`echo "http2=false" >> /etc/dnf/dnf.conf`），但这不是推荐的长期方案，应优先由基础设施团队修复服务端问题。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 软件源镜像（`repo.****.org`）在 CI 构建时段（2026-07-09 14:47 UTC 前后）是否存在已知的 HTTP/2 服务中断或 CDN 节点故障。
- 可对比同期其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 PR 是否也因相同原因失败，以确认影响范围。
