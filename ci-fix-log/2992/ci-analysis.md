# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2 仓库下载中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, openEuler 24.03-LTS-SP4, dnf install

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
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`RUN dnf install` 步骤）
- 失败原因: CI 构建环境在从 `repo.****.org`（openEuler 24.03-LTS-SP4 仓库）下载 RPM 包时，遭遇多次 HTTP/2 流错误（Curl error 92: Stream error in the HTTP/2 framing layer, INTERNAL_ERROR），`gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 在所有镜像重试耗尽后仍未下载成功，导致 dnf 安装失败（exit code: 1）。

### 与 PR 变更的关联
**与 PR 变更无关**。本 PR 仅新增 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及对应元数据条目（README.md、image-info.yml、meta.yml），Dockerfile 内容正确（基础镜像、dnf 包列表、编译步骤、多阶段构建均无语法或逻辑错误）。失败直接原因是 openEuler 24.03-LTS-SP4 仓库在构建时刻出现 HTTP/2 协议层面的连接异常，任何需要从该仓库下载软件包的构建都会受此影响。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。此为 CI 基础设施网络问题（`infra-error`），与代码变更无关。应在构建环境网络恢复正常后重新触发 CI 流水线（re-run / retry）。若问题持续出现，需联系 CI 基础设施团队排查 `repo.****.org` 仓库服务器的 HTTP/2 配置或 CI runner 到仓库之间的网络链路上是否存在 HTTP/2 协议兼容性问题。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在构建时刻是否存在 HTTP/2 服务端异常或负载过高导致流中断。
- CI 构建环境中 HTTP/2 代理（如果有）是否存在连接保持策略不当的问题。
- 是否有其他同样依赖 `openeuler:24.03-lts-sp4` 基础镜像的并发构建加剧了仓库连接压力。

## 修复验证要求
（不适用 — 本次失败为 infra-error，无需修改任何代码文件）
