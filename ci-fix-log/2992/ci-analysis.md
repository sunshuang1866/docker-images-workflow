# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2帧错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
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
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在 HTTP/2 传输层出现帧错误（Curl error 92），导致多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`gcc`、`guile` 等）下载失败，最终 `No more mirrors to try`，dnf 安装步骤以退出码 1 失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`（47 行新 Dockerfile）以及对应的 README、image-info.yml、meta.yml 更新。Dockerfile 的 `dnf install` 命令语法正确，包名均合法，与同目录下 SP3 版本保持一致的依赖模式（仅基础镜像 TAG 从 `24.03-lts-sp3` 变为 `24.03-lts-sp4`）。失败完全由 openEuler 官方仓库镜像的网络/HTTP2 协议层问题引起，是 CI 基础设施问题，非代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 该失败是 openEuler 24.03-LTS-SP4 仓库镜像的瞬时网络问题（HTTP/2 帧错误）。Dockerfile 代码本身无问题，重新触发 CI 构建即可，无需任何代码修改。如果仓库镜像持续不稳定，可考虑在 `dnf` 命令前添加重试配置（如 `echo 'retries=10' >> /etc/dnf/dnf.conf` 或 `echo 'timeout=300' >> /etc/dnf/dnf.conf`），但这属于锦上添花而非必要修复。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 的仓库镜像（`repo.****.org`）在构建时段是否有已知的网络问题或维护窗口。
- 同仓库其他同样使用 `openeuler:24.03-lts-sp4` 基础镜像的 Dockerfile 是否在同批次 CI 中也出现了相同错误——如果是，可确认是仓库镜像全局故障而非 PR 特有问题。
- 需要注意 #7（stage-1 的 `dnf install`）和 #8（builder 的 `dnf install`）两个构建阶段同时遭遇了 repo 镜像的 HTTP/2 错误，但 #7 尚未走到最终失败就被 #8 的失败触发 CANCELED，这表明问题影响范围覆盖了同一个 repo 的多次独立下载请求。
