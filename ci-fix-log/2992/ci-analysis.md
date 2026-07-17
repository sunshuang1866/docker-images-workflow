# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库（`repo.****.org`）的 HTTP/2 连接不稳定，多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）在下载过程中遭遇 HTTP/2 stream 异常关闭（`INTERNAL_ERROR`），经过多轮镜像重试后仍无法成功下载 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`（34MB），导致 dnf 安装失败。该问题在并行的 builder 阶段（#8）和 stage-1 阶段（#7）同时出现，属于仓库服务端问题。

### 与 PR 变更的关联
与 PR 代码变更**无关**。该 PR 仅新增了一个标准格式的 Dockerfile（`dnf install` 构建依赖 → 编译安装 → 多阶段复制），Dockerfile 语法和包名均正确。失败原因为 openEuler 24.03-LTS-SP4 仓库服务端的 HTTP/2 连接层间歇性中断，属于 CI 基础设施问题，任何依赖该仓库的构建均可能触发。

## 修复方向

### 方向 1（置信度: 高）
无需修改代码。这是 openEuler 仓库镜像站 HTTP/2 服务端的临时故障，应**重试 CI**（rerun the failed job）。若持续复现，可考虑在 Dockerfile 的 `dnf install` 前添加 `dnf config-manager` 或 `echo` 配置将仓库连接协议降级为 HTTP/1.1（绕过 HTTP/2 framing layer 问题），但这是规避方案而非根因修复。

## 需要进一步确认的点
- 若多次重试 CI 仍然失败，需确认 openEuler 24.03-LTS-SP4 仓库 `repo.****.org` 的 HTTP/2 服务是否存在持续性问题或配置变更。
- 同期其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也出现相同故障，以确认是否为仓库侧全局性问题。
