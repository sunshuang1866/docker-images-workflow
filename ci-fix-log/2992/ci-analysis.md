# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 包仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel`，即 builder 阶段的第一个 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的官方软件仓库（`repo.****.org`）在 CI 构建期间发生 HTTP/2 传输层故障，多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载时 HTTP/2 流被服务端异常关闭（`INTERNAL_ERROR`），其中 `gcc` 重试所有镜像均失败后，dnf 安装以 exit code 1 退出。这是一个 CI 基础设施侧的网络/仓库服务暂时性问题，Dockerfile 本身语法和指令均正确。

### 与 PR 变更的关联
**完全无关**。PR #2992 的变更内容仅为：
1. 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（SP4 版本构建文件）
2. 更新 `Others/multiwfn/README.md`、`doc/image-info.yml`、`meta.yml` 三个元数据文件以登记新镜像

Dockerfile 中的 `dnf install` 命令语法完全正确（依赖包名均存在于 SP4 仓库的包列表中），失败原因是 openEuler SP4 官方仓库的 HTTP/2 服务在构建时刻不可用。同一时刻运行的 `#7`（runtime stage 的 dnf install）也遭受了相同的 HTTP/2 流错误，进一步证实这是仓库侧问题而非 Dockerfile 写法问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，触发重试即可。** 这是 CI 基础设施的暂时性故障——openEuler SP4 软件仓库的 HTTP/2 服务在构建窗口期内不稳定。在仓库恢复稳定后重新触发 CI 构建（retry）即可通过。不需要对 PR 中的任何文件做改动。

## 需要进一步确认的点
- 无。错误特征（`Curl error (92): Stream error in the HTTP/2 framing layer` + `INTERNAL_ERROR`）明确指向服务器端 HTTP/2 协议层故障，与 Dockerfile 内容、PR 代码变更均无关联。这是典型且诊断清晰的 infra-error。
