# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, MIRROR, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: 新增文件 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`:7（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像在构建期间反复出现 HTTP/2 帧层错误（Curl error 92: INTERNAL_ERROR），多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）在多个镜像节点上均下载失败，dnf 耗尽所有镜像后放弃，导致构建终止。这是仓库服务器侧的瞬态网络故障，与 Dockerfile 内容无关。

### 与 PR 变更的关联
PR 新增了一个 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`），其 `RUN dnf install` 步骤需要从 openEuler 24.03-LTS-SP4 仓库下载约 157 个 RPM 包。构建时仓库镜像遭遇 HTTP/2 连接异常，属于 CI 基础设施问题，**与 PR 代码变更无关**。Dockerfile 语法正确，基镜像拉取（`FROM openeuler/openeuler:24.03-lts-sp4`）成功，且 PR 仅新增文件无修改已有代码，不会引入回归。

## 修复方向

### 方向 1（置信度: 高）
CI 基础设施问题，无需修改代码。直接**重新触发 CI 构建**即可。当 openEuler 24.03-LTS-SP4 仓库镜像恢复稳定后，`dnf install` 步骤应能正常下载 RPM 包并完成构建。

## 需要进一步确认的点
- 确认构建时 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）是否存在全网性故障或升级维护。
- 如果重试多次仍失败，需确认 CI runner 所在网络环境是否与仓库镜像节点间存在 HTTP/2 协议兼容性问题（可尝试降级为 HTTP/1.1）。
