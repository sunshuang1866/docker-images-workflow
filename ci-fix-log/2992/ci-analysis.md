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

#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像在提供 RPM 包下载时，多次返回 HTTP/2 协议层错误（`INTERNAL_ERROR err 2`），导致 `dnf` 重试全部镜像后仍无法完成若干关键包（`gcc`、`gcc-gfortran`、`glibc-devel`、`guile` 等）的下载。构建阶段的 `#8 builder`（157 个包）因 `gcc` 下载彻底失败而终止，运行时阶段 `#7 stage-1`（32 个包）虽同样遭遇错误但因构建失败而被连带取消。

### 与 PR 变更的关联
本次 PR 与失败无关。PR 仅新增了 MultiWFN 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中 `dnf install` 命令语法和包名均正确。失败根因是 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 服务器端协议异常，属于 CI 基础设施问题，重试构建即可。

## 修复方向

### 方向 1（置信度: 高）
无需修改代码。此为 CI 基础设施中的软件仓库镜像服务器 HTTP/2 协议故障（`Curl error 92: INTERNAL_ERROR`），属于临时性网络问题。直接重新触发 CI 构建即可。如果反复出现，需联系 openEuler 仓库运维方排查 24.03-LTS-SP4 仓库的 HTTP/2 服务稳定性。

## 需要进一步确认的点
- 无需进一步确认。日志中 Curl error (92) HTTP/2 INTERNAL_ERROR 证据充分，错误完全来自仓库服务器端，与 PR 代码无关。
