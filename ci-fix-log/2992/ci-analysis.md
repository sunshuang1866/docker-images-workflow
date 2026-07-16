# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install` 命令）
- 失败原因: openEuler 24.03-LTS-SP4 的官方 RPM 仓库镜像（`repo.****.org`）在本次构建期间 HTTP/2 连接不稳定，多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载时遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer`。其中 `gcc` 包（34 MB）的下载在多次重试后耗尽所有镜像，`dnf install` 最终失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了标准的 Dockerfile、README 更新、meta.yml 及 image-info.yml，Dockerfile 中的 `dnf install` 命令语法和包列表均无问题。失败由 openEuler 仓库镜像服务器的 HTTP/2 协议层网络故障（`INTERNAL_ERROR (err 2)`）引起，属于 CI 基础设施层面的瞬时故障。

证据：
1. 两个并行阶段（builder `#8` 的 157 个包和 stage-1 `#7` 的 32 个包）均出现 HTTP/2 stream error，说明问题在服务端而非某一特定包
2. `#7` 阶段虽然重试后成功下载了 `glibc-devel`，但也曾遭遇同类错误（`#7 1268.5` 和 `#7 1598.9`），进一步确认仓库服务端不稳定
3. Dockerfile 内容自身无语法错误、包名错误或依赖缺失——`#7` 阶段依赖解析和大部分包下载均正常完成，仅在特定包下载时触发 HTTP/2 错误

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是 openEuler 仓库镜像服务器的瞬时 HTTP/2 连接故障，属于 infra-error。Code Fixer 无需处理。

建议操作：等待仓库镜像恢复后重新触发 CI 构建（retry），或人工确认 `repo.****.org` 的 HTTP/2 服务状态已恢复正常后再触发。

## 需要进一步确认的点
- 确认 `repo.****.org` 的 HTTP/2 服务在构建时段是否存在已知中断
- 若多次 retry 仍失败，考虑是否为仓库镜像对特定源 IP 的 HTTP/2 流控/限流策略导致，需联系基础设施团队排查
