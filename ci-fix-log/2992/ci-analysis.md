# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, Error downloading packages

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 What is that? [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `dnf install`）
- 失败原因: openEuler 24.03-LTS-SP4 软件源在构建期间出现 HTTP/2 流帧层错误（`Curl error (92)`），多个 RPM 包（`gcc-gfortran`、`guile`、`gcc`）下载过程中遭遇 `INTERNAL_ERROR`，经过多次镜像重试后 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 耗尽所有镜像源仍下载失败，导致 `dnf install` 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（以及配套的 README、image-info.yml、meta.yml 更新）。Dockerfile 语法和内容均正确（与已有的 SP3 Dockerfile 模式一致）。失败完全由 openEuler 24.03-LTS-SP4 软件仓库的网络/服务端问题触发——`#8`（builder 阶段）和 `#7`（stage-1 阶段）均出现 HTTP/2 流错误，且 `#7` 阶段也有 `glibc-devel` 和 `gcc-gfortran` 的同类型 Curl error (92)，说明仓库服务端存在间歇性 HTTP/2 连接中断。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重新触发 CI 构建即可。** 此为 openEuler 24.03-LTS-SP4 软件仓库的临时性网络/服务端故障（HTTP/2 流帧层错误），与 Dockerfile 内容无关。等仓库服务恢复后，重新运行 CI 应能通过。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）在构建时段是否存在已知的服务中断或网络波动。
- 若重试后仍持续失败，需确认仓库 HTTP/2 配置是否与 CI 构建环境的 curl 版本存在兼容性问题（可尝试强制降级到 HTTP/1.1）。
