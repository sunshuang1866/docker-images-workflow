# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM源HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, HTTP/2 stream

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方 RPM 仓库镜像在 CI 构建时发生 HTTP/2 协议层错误（`INTERNAL_ERROR`），导致多个 RPM 包下载中断，最终 `gcc-12.3.1-110.oe2403sp4` 在耗尽所有 mirror 重试后仍下载失败，`dnf` 返回退出码 1。

### 与 PR 变更的关联

**与 PR 变更无关。** 本次 PR 仅新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（一个标准的多阶段构建 Dockerfile）以及 README、image-info.yml、meta.yml 的配套元数据更新。失败的根因是 openEuler 24.03-LTS-SP4 RPM 仓库服务器自身在网络层（HTTP/2 流）出现间歇性故障，属于 CI 基础设施问题。日志中可观察到两个并行构建阶段（`#7` stage-1 和 `#8` builder）均遭遇相同类型的 Curl error (92)，进一步证明这是仓库端问题而非代码问题。

## 修复方向

### 方向 1（置信度: 高）
**这是 CI 基础设施问题，无需修改代码。** 应重试 CI 构建。如果仓库镜像的 HTTP/2 问题是暂时的，下次构建将自动通过。如果问题持续出现，需联系 openEuler 24.03-LTS-SP4 仓库运维方排查 HTTP/2 代理层故障。

## 需要进一步确认的点
- 该问题是偶发性的还是持续性的——可通过 CI 手动重试来验证。
- 如果重试仍失败，需确认 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在 CI 构建网络环境中的可达性和 HTTP/2 协议兼容性。
