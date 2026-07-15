# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: CI 构建环境中 openEuler 24.03-LTS-SP4 的 RPM 仓库镜像服务端存在 HTTP/2 协议层故障（`INTERNAL_ERROR`），导致多个大体积 RPM 包（`gcc-gfortran` 13 MB、`glibc-devel` 2 MB、`guile` 6.3 MB、`gcc` 34 MB）在下载过程中反复遭遇 `Curl error (92)` 流中断。虽然部分包经重试最终成功下载，但 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`（34 MB）在耗尽所有可用镜像后仍无法完成下载，导致 `dnf install` 失败。

注意：并行构建的 stage-1（`#7`）同样遭遇多次 HTTP/2 流错误（`glibc-devel`、`gcc-gfortran`），但因 builder stage（`#8`）率先失败，BuildKit 随后取消了 stage-1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准格式的 Dockerfile，其 `dnf install` 命令语法正确、包名均有效。失败完全由 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 服务端协议故障引起，属于 CI 基础设施层面的临时性问题，与代码逻辑、包依赖策略均无关联。

## 修复方向

### 方向 1（置信度: 高）
**此为 infra-error，无需修改任何代码。** 直接触发 CI 重跑即可。如果重跑后仍然失败，则需联系 openEuler 仓库镜像运维团队排查 `repo.****.org` 的 HTTP/2 服务端问题（可能涉及 CDN 节点或负载均衡器的 HTTP/2 帧处理 bug）。

## 需要进一步确认的点
- 该 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 问题是否为持续性故障：可尝试手动在 CI runner 上执行 `curl -I --http2 https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/` 验证 HTTP/2 连接是否正常。
- 其他基于 `openeuler/openeuler:24.03-lts-sp4` 的镜像构建是否也受到同样影响——若多个 PR 同时报同类错误，则确认是仓库端问题。
