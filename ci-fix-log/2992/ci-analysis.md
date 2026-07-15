# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（dnf install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件源镜像在 CI 构建期间出现 HTTP/2 连接的不稳定问题，`dnf` 尝试从多个镜像下载 RPM 包（gcc、gcc-gfortran、glibc-devel、guile 等）均因 `Curl error (92): Stream error in the HTTP/2 framing layer` 失败，最终所有镜像均不可用，构建中止。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 仅新增了一个 Dockerfile 及配套的 README、image-info.yml、meta.yml 条目，这些变更是纯粹的声明性元数据，不包含任何可能导致网络层错误的代码。失败原因为 CI 运行时 openEuler 24.03-LTS-SP4 软件源不可用，属于基础设施问题。

值得注意的是，同一个构建任务中，stage-1 阶段（`#7`，安装 gcc-gfortran、make、openblas-devel、lapack-devel）也遭遇了相同的 HTTP/2 流错误（glibc-devel、gcc-gfortran 等），进一步证实这是仓库源的普遍性问题，而非 builder 阶段专属。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败是 openEuler 24.03-LTS-SP4 软件源镜像的瞬态网络故障（HTTP/2 流中断），属于 infra-error。Dockerfile 本身无逻辑错误——同一 PR 中 stage-1 阶段（仅安装 32 个包）已成功下载了大部分包（如 compat-openssl11-libs、binutils、cpp、gcc、lapack、lapack-devel 等），只是在下载 gcc-gfortran 和 glibc-devel 时也遇到 HTTP/2 错误。等待软件源恢复后重试即可。

## 需要进一步确认的点

- 确认 openEuler 24.03-LTS-SP4 软件源镜像（`repo.****.org`）在 CI 构建时间段（2026-07-09 14:46-14:49 UTC 前后）是否存在已知的服务降级或维护事件。
- 检查其他同时间段使用同一软件源的 PR 构建是否也遇到了类似的 `Curl error (92)` 失败，以排除是否为单点 runner 网络问题。
