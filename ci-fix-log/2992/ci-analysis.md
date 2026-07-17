# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), [MIRROR], No more mirrors to try, dnf install

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
ERROR: failed to solve: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方 RPM 仓库（`repo.****.org`）的 HTTP/2 服务端持续返回 `INTERNAL_ERROR (err 2)` 流协议错误，导致多个 RPM 包（gcc-gfortran、glibc-devel、guile）下载中断，最终 gcc（34 MB 大包）在所有镜像重试耗尽后彻底失败。这种现象在同一个构建中同时影响 builder 阶段（#8，157 个包）和 stage-1 阶段（#7，32 个包），且横跨不同包、不同 HTTP/2 stream ID，表明根因在仓库服务端而非 CI 运行环境。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`）及配套的元数据和文档条目，Dockerfile 格式与语法均无问题。失败完全由 openEuler 24.03-LTS-SP4 的 RPM 镜像仓库 HTTP/2 服务不稳定所致。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建即可。** 这是一个典型的仓库服务端临时性故障（HTTP/2 INTERNAL_ERROR），属于基础设施问题。等待仓库恢复后重新触发 CI job，大概率可以通过。

### 方向 2（置信度: 低）
如果仓库 HTTP/2 问题持续，可在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager` 配置降低 HTTP 协议版本或增加重试次数，但这不是推荐方案——根因在服务端，应从基础设施层面解决。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 的 RPM 仓库（`repo.****.org`）是否存在已知的 HTTP/2 服务稳定性问题
- 该仓库是否有备用镜像（如 `repo.huaweicloud.com`）可以作为 `dnf install` 的回退源
- arm64 (aarch64) 架构的构建是否也会遇到同样的仓库问题（日志中仅包含 x86-64 构建）
