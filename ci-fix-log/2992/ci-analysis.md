# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, [FAILED], No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...(retry failed)
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...(retry failed)
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤）
- 失败原因: CI 构建环境在通过 dnf 从 openEuler 24.03-LTS-SP4 仓库镜像下载 RPM 包时，多次出现 Curl error (92) — HTTP/2 流被异常关闭（`INTERNAL_ERROR`），服务端或中间代理的非正常流终止。受影响包包括 `gcc-gfortran`、`glibc-devel`、`guile`、`gcc`。其中 `gcc`（34 MB）重试耗尽所有镜像后最终下载失败，导致整个 `dnf install` 步骤退出码 1。同时 stage-1（运行时阶段）的 `dnf install` 也遭遇同类错误（`glibc-devel`、`gcc-gfortran`），并在 builder 阶段失败后被 CANCELED。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 multiwfn 在 openEuler 24.03-lts-sp4 上的 Dockerfile（以及对应的 README、meta.yml、image-info.yml 条目），Dockerfile 本身的语法和依赖声明均正确（与已有的 sp3 版本 Dockerfile 结构一致）。失败完全由上游 openEuler 24.03-LTS-SP4 仓库镜像的网络/HTTP2 协议层问题导致，属于 CI 基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是一个 CI 基础设施层面（上游仓库镜像 HTTP/2 协议层异常）的临时性故障。建议操作：
- 重新触发 CI 构建（retry），等待上游仓库镜像恢复
- 若多次 retry 均失败，排查 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）的 HTTP/2 前端代理或 CDN 是否存在异常

## 需要进一步确认的点
- 确认 CI 构建时间点 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库）的 CDN/代理层是否存在已知中断或维护事件
- 建议在 CI 非高峰期重新触发构建，确认是否为临时性网络波动

## 修复验证要求
不适用（infra-error，无需代码修复）。
