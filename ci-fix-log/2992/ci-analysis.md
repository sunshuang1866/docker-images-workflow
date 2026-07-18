# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤，builder 阶段）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像 `repo.****.org` 在 CI 构建期间出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），导致 `gcc`、`gcc-gfortran`、`guile` 等多个 RPM 包下载失败，所有镜像重试耗尽后 `dnf install` 退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本 PR 的改动仅为新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、image-info.yml、meta.yml），这些文件结构正确、符合规范。失败完全由 CI 构建环境与 openEuler RPM 仓库之间的网络问题（HTTP/2 流传输异常）引起，非代码缺陷。

值得注意的是，stage-1（最终运行阶段）的 `dnf install`（步骤 #7）虽然部分包也遇到 `[MIRROR]` 警告（`glibc-devel`、`gcc-gfortran`），但由于所需包数量少（32 个 vs builder 阶段的 157 个），大部分包仍成功下载。builder 阶段因包数量多、重试耗尽而率先失败，导致 stage-1 被 `CANCELED`。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码。** 这是一个 CI 基础设施的暂时性网络问题。直接重试 CI job 即可——HTTP/2 流错误通常是仓库服务器侧的瞬时问题，在后续运行中可能不再复现。PR 的 Dockerfile 及元数据变更本身没有错误。

## 需要进一步确认的点
- 确认 `repo.****.org` 仓库在 CI 失败时段是否存在已知的 HTTP/2 服务端问题或负载过高导致的流中断。
- 如果该问题频繁复现（同一仓库在多个不同 PR 的构建中反复出现 Curl error 92），可考虑在 CI 构建环境中配置 `dnf` 回退到 HTTP/1.1（如设置 `http2=false` 于 dnf 仓库配置中）或切换到其他镜像源。
