# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: SP4仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf, gcc, SP4

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `RUN dnf install` 指令）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在 HTTP/2 协议层频繁出现流错误（Curl error 92: INTERNAL_ERROR），导致多个包（gcc-gfortran、glibc-devel、guile、gcc）下载失败。gcc 包在反复重试后耗尽所有镜像，dnf 最终报错退出。构建的 builder 阶段（#8，157 个包）和 stage-1 阶段（#7，32 个包）均受到 HTTP/2 流错误影响，stage-1 阶段因 builder 阶段先失败而被取消。

### 与 PR 变更的关联
与 PR 变更无关。PR 仅新增了一个标准 Dockerfile（安装 git、gcc、gfortran 等基础工具）及相关元数据更新。DNS 安装命令本身无语法或逻辑错误，失败完全由外部仓库 HTTP/2 网络层问题引起。

## 修复方向

### 方向 1（置信度: 中）
**重试即可**。该失败为 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 协议层间歇性故障，属于基础设施层面的瞬时问题。可以 re-run CI job 重试构建，等待仓库镜像恢复。无需修改任何代码。

### 方向 2（置信度: 低）
如果问题持续复现，可在 Dockerfile 的 dnf 命令前添加 `dnf config-manager --setopt=max_parallel_downloads=1` 降低并发下载数，或添加 `--setopt=retries=10` 提高重试次数，减轻 HTTP/2 多路复用下的流错误影响。但由于 gcc 包（34MB）下载时间较长且流错误概率较高，此方向不能完全消除问题。

## 需要进一步确认的点
1. 验证 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）的 HTTP/2 服务是否已恢复正常，可通过 `curl -I --http2 https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/` 测试连通性
2. 确认该 SP4 仓库镜像的同类问题是否为近期频发（若频发，建议提升到 CI 基础设施团队处理）
