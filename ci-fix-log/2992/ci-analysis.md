# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, dnf, MIRROR, No more mirrors to try

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
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 软件仓库（`repo.****.org`）在提供多个软件包下载时反复出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），经过多次镜像重试后仍无法完成 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 的下载，导致 dnf 安装失败。

### 与 PR 变更的关联
**与 PR 无关**。PR #2992 仅新增了一个常规的 multiwfn Dockerfile（对应 openEuler 24.03-LTS-SP4 基础镜像），Dockerfile 本身结构正确，与已有的 `24.03-lts-sp3` 版本 Dockerfile 模式一致。失败纯粹由 CI 构建过程中 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 传输异常导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该失败为 openEuler 24.03-LTS-SP4 仓库服务器的临时性 HTTP/2 流错误，PR 代码无问题。等待仓库服务恢复稳定后重新触发 CI 构建即可。

### 方向 2（置信度: 低）
**调整 dnf 配置以规避 HTTP/2 问题**。如果仓库 HTTP/2 问题持续出现，可在 Dockerfile 中为 dnf 添加 `--setopt=proxy=_none_` 或配置 dnf 使用 HTTP/1.1 协议（如 `echo 'http2=false' >> /etc/dnf/dnf.conf`），但这是临时规避手段，优先建议方向 1。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）的 HTTP/2 服务端是否已恢复稳定
- 如果多次重试 CI 均失败且同一时段其他基于 24.03-LTS-SP4 的 PR 构建也出现相同错误，则可能需要反馈给仓库运维团队
