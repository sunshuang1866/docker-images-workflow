# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（docker build builder 阶段 `dnf install` 步骤）
- 失败原因: CI 构建环境在通过 dnf 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，遭遇大量 HTTP/2 协议层流错误（Curl error 92: INTERNAL_ERROR），多个不同包（gcc-gfortran、glibc-devel、guile、gcc）在多个 HTTP/2 连接流上均报 `stream was not closed cleanly`。dnf 重试耗尽所有镜像后，`gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 下载失败，导致整个 builder 阶段的 `dnf install` 命令退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（47 行新增）及配套的元数据文件更新（README.md、image-info.yml、meta.yml）。Dockerfile 本身语法和依赖声明正确——`dnf install` 所需的所有包名（`git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel`）均为 openEuler SP4 仓库中实际存在的包（日志中 `#7` stage-1 阶段已成功解析所有 32 个依赖包并下载了部分）。失败纯粹是仓库镜像的网络传输问题。

值得注意的是，`#7`（stage-1，运行阶段）和 `#8`（builder，构建阶段）两个 Docker 构建阶段**同时**遭遇 HTTP/2 流错误，且涉及不同包、不同 HTTP/2 stream ID，进一步排除了单个包损坏或特定镜像节点问题的可能性，指向 openEuler SP4 仓库整体在构建时刻存在 HTTP/2 层面的服务端异常。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码。** 这是 CI 基础设施/上游仓库镜像的网络瞬态故障。应触发 CI 重新构建（retry），等待仓库镜像 HTTP/2 服务恢复正常后构建即可通过。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库在构建时间点是否存在已知的 HTTP/2 服务中断或负载问题。
- 确认该失败是否只在单次构建中出现（若是，进一步佐证为瞬态网络故障）；若多次重试均失败，需检查 CI 构建节点到 openEuler 仓库的网络连通性。
