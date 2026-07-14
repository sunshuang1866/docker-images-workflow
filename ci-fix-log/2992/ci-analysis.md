# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2帧错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, repo.*.org, dnf install, openEuler-24.03-LTS-SP4

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库（`repo.****.org`）在构建期间出现 HTTP/2 帧层传输错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载失败。`#8`（builder 阶段）最终因 `gcc` 包所有镜像均重试失败而中止，`#7`（stage-1 阶段）被连锁取消。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 multiwfn 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套文档更新。Dockerfile 中的 `dnf install` 命令语法和包名均正确，失败完全由 openEuler 包仓库在构建期间的 HTTP/2 传输故障引起。CI 需要重试。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施问题，**Code Fixer 无需处理代码**。应重新触发 CI 构建（retry），待 openEuler 24.03-LTS-SP4 仓库镜像恢复 HTTP/2 连接稳定性后即可通过。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 软件包仓库（`repo.****.org`）的 HTTP/2 服务在构建时段的可用性状态。
- 如果重试后仍然失败，需排查 CI runner 网络到 openEuler 仓库的网络链路是否存在 HTTP/2 协议兼容性问题（如中间代理或负载均衡器对 HTTP/2 的支持）。
