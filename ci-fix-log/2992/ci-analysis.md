# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（builder 阶段的 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）在 Docker 构建过程中出现 HTTP/2 协议层错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载失败。`gcc` 包（34 MB）在尝试所有镜像镜像后均下载失败，导致 `dnf install` 退出码 1，Docker 构建中断。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（内容正确，语法无误）及相关元数据文件（README.md、image-info.yml、meta.yml）。失败的原因是 openEuler 软件仓库的 HTTP/2 服务端在构建时发生间歇性流错误，属于 CI 基础设施问题。日志中 stage-1（`#7`）阶段的 `dnf install` 也出现了相同的 `[MIRROR]` 错误（`glibc-devel`、`gcc-gfortran`），但因其包体积较小或重试时机更有利而成功恢复，进一步印证这是服务端网络波动而非 Dockerfile 内容问题。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试**。该失败是 openEuler 软件仓库 HTTP/2 协议的间歇性错误，与 PR 代码变更无关。重新触发 CI 流水线即可，无需修改任何代码或 Dockerfile。若多次重试均因同类错误失败，则需联系 openEuler 仓库基础设施团队排查 `repo.****.org` 的 HTTP/2 服务配置。

## 需要进一步确认的点
- 无。日志中错误信息清晰且完整，足以判断为 `infra-error`。stage-1（`#7`）的 `[MIRROR]` 警告和 stage-2（`#8`）的 `[FAILED]` 均指向同一仓库的 HTTP/2 协议问题。

## 修复验证要求
无需验证。此失败为基础设施问题，重试 CI 即可。如需确认仓库恢复情况，可手动 `curl` 测试日志中问题 RPM 包的下载（如 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`）是否恢复正常。
