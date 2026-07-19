# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: OS 仓库 HTTP/2 传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 OS 软件包仓库（`repo.****.org`）发生 HTTP/2 协议层传输错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载时被 HTTP/2 流异常中断。所有镜像源重试耗尽后，`gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 最终无法下载，导致 `dnf install` 失败（exit code: 1）。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据（README.md、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令为标准包安装操作，与已存在的 SP3 版本 Dockerfile 结构一致。失败完全由 openEuler OS 软件包仓库的 HTTP/2 传输层故障引起，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，触发重试即可。** 该失败是 openEuler 24.03-LTS-SP4 软件包仓库在镜像拉取期间的瞬时网络故障（HTTP/2 流异常中断），与 Dockerfile 或 PR 变更无关。待仓库恢复后重新触发 CI 构建即可通过。

## 需要进一步确认的点
- 确认 `repo.****.org`（openEuler 24.03-LTS-SP4 OS 仓库）的 HTTP/2 服务是否已恢复正常。可以手动尝试 `curl -I` 请求该仓库中的任意 RPM 包地址验证。
- 如果多次重试后仍然失败，需确认 CI 构建节点到该仓库的网络链路是否存在持续性故障，或仓库是否变更了访问策略（如限流、强制 HTTP/1.1 等）。

## 修复验证要求
无需代码修复，因此无需额外验证步骤。
