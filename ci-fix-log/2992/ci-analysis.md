# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`
- 失败原因: Docker 构建过程中 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时，仓库镜像服务器返回 HTTP/2 `INTERNAL_ERROR`（Curl error 92），多个包（gcc-gfortran、glibc-devel、guile、gcc）均受影响，最终 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 耗尽所有镜像重试机会后下载失败，导致构建终止（exit code: 1）。这是仓库镜像服务端的 HTTP/2 协议层临时故障，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 变更仅新增了 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件。Dockerfile 中 `dnf install` 的命令语法和包名均为合法。失败的根本原因是 **openEuler 24.03-LTS-SP4 官方仓库镜像服务端出现 HTTP/2 流错误（INTERNAL_ERROR）**，属于 CI 基础设施层面的临时性网络/服务端问题，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 中）
重新触发 CI 构建。由于失败原因为仓库镜像服务端的临时性 HTTP/2 协议错误，且日志中多个不同 RPM 包在不同时刻、不同 HTTP/2 流上均出现相同错误，高度提示为服务端瞬时故障。若仓库镜像服务已恢复，重试即可通过。

### 方向 2（置信度: 低）
若重试仍然失败，可尝试在 Dockerfile 中为 `dnf` 命令添加重试机制（如 `dnf install --setopt=retries=10 --setopt=timeout=30 ...`），或显式指定其他 openEuler 镜像仓库地址以绕过存在 HTTP/2 兼容性问题的特定镜像节点。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库 `repo.****.org` 在 CI 构建环境中的网络可达性和 HTTP/2 兼容性状态。
- 如该问题持续出现，需要确认 24.03-LTS-SP3 等其他版本仓库（同批次 CI 构建）是否也出现相同问题，以排除是否为仓库侧的系统性变更。
