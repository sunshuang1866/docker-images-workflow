# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库 HTTP/2 流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败原因: openEuler 24.03-LTS-SP4 官方软件仓库（`repo.****.org`）在构建期间出现 HTTP/2 协议传输故障，多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载时遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer (INTERNAL_ERROR)`。dnf 尝试了所有可用镜像后仍失败，最终 `gcc` 包无法下载导致整个 `dnf install` 命令以 exit code 1 退出。Dockerfile 中 `builder` 阶段（#8）和 `stage-1` 阶段（#7）的两个 `dnf install` 均受此影响，阶段 #7 被连带取消（CANCELED）。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile` 以及对应的 README、`image-info.yml`、`meta.yml` 条目。Dockerfile 中的 `dnf install` 命令语法正确，包名均为 openEuler 24.03-LTS-SP4 仓库中的合法包。失败完全由构建时 openEuler 仓库服务器的 HTTP/2 传输层故障所致——其他正常下载的包（如 `binutils`、`cpp`、`gcc-c++` 等）来自同一仓库但恰好未触发流错误，进一步证明这是间歇性服务端问题而非 Dockerfile 配置错误。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 即可。** 该失败为 openEuler 24.03-LTS-SP4 官方软件仓库的瞬时 HTTP/2 传输故障，属于基础设施问题。Dockerfile 本身配置正确。等待仓库恢复后重新触发 CI 构建（如 `/retest` 或重新 push），本次失败应该不再复现。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在构建时间点（2026-07-09 14:46~14:47 UTC）是否存在已知的 CDN/服务器故障或维护事件。
- 如果多次重试后仍出现相同的 HTTP/2 流错误，则需确认该仓库的 HTTP/2 支持是否存在持续性问题，此时可考虑在 Dockerfile 中为 `dnf` 配置 `http2=false` 或切换到 HTTP/1.1 连接。
