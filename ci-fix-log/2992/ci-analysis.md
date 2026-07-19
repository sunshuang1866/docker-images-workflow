# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 dnf install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件源镜像服务器存在 HTTP/2 流传输故障，多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载过程中遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer`，dnf 在耗尽所有重试镜像后放弃。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了 multiwfn 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据（meta.yml、README.md、image-info.yml）。失败根因是 CI 构建环境中 openEuler 24.03-LTS-SP4 软件源镜像服务器的 HTTP/2 层发生了临时性故障，属于基础设施问题。该故障同时影响了 builder 阶段（#8）和 runtime 阶段（#7）的 dnf 包下载，覆盖多个不同的 RPM 包。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 这是一个基础设施级别的 repo 镜像服务器网络故障。建议直接重新触发 CI 构建（retry），待 openEuler 24.03-LTS-SP4 软件源镜像恢复正常后构建即可通过。

## 需要进一步确认的点
- 无需进一步确认。日志已明确指向软件源 HTTP/2 流层故障，与 PR 代码变更无关。若重试后仍失败，需排查 CI 网络链路到 `repo.****.org` 的 HTTP/2 连接稳定性。
