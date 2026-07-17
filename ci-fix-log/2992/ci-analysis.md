# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf install, MIRROR, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:7-10（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像 (`repo.****.org`) 在构建期间出现 HTTP/2 流层协议错误（Curl error 92），多个 RPM 包（`gcc-gfortran`、`guile`、`gcc`）下载遭遇 `HTTP/2 stream not closed cleanly: INTERNAL_ERROR`，其中 `gcc` 包在所有镜像均重试失败后触发构建终止。两个并行构建阶段（#7 运行时阶段、#8 builder 阶段）均在下载 package 时遭遇相同类型的 Curl error，确认问题出在仓库服务端，而非客户端网络。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 multiwfn 24.03-lts-sp4 的 Dockerfile 及配套元数据，Dockerfile 中的 `dnf install` 命令语法正确、包名正确（与已有的 24.03-lts-sp3 版本结构一致）。失败是 openEuler 软件仓库镜像服务器的临时性 HTTP/2 协议层故障导致 RPM 包无法下载，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 此为 openEuler 软件仓库镜像服务的临时性故障（HTTP/2 流异常断开），建议在仓库服务恢复后重新触发 CI 构建。同类 PR 在仓库正常时可构建成功。

## 需要进一步确认的点
- 确认 `repo.****.org` 仓库服务的当前状态是否已恢复正常
- 确认 CI 构建环境与仓库镜像之间的网络连通性是否存在持续性问题
