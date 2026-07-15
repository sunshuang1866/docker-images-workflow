# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）在 CI 构建期间出现 HTTP/2 协议层面的流传输错误（Curl error 92），导致多个 RPM 包（gcc、gcc-gfortran、glibc-devel、guile 等）下载失败，dnf 在耗尽所有镜像重试后放弃安装。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增的 Dockerfile 本身语法正确（`dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel` 是合理的依赖声明），失败纯粹是 openEuler 24.03-LTS-SP4 的软件仓库在构建发生时存在临时性 HTTP/2 网络问题。日志中 `#7`（运行时阶段的 dnf install，仅 32 个包）在下载过程中也遇到了相同的 `[MIRROR]` 流错误（gcc-gfortran、glibc-devel），进一步佐证这是仓库侧的普遍问题。

## 修复方向

### 方向 1（置信度: 高）
本次为 CI 基础设施/上游仓库临时故障，与代码变更无关。**无需修改 Dockerfile**。等待 openEuler 24.03-LTS-SP4 软件仓库的 HTTP/2 服务恢复正常后，重新触发 CI 构建即可。如果问题持续复现，可考虑联系 openEuler 镜像站运维排查 HTTP/2 服务器配置。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）当前的 HTTP/2 服务状态是否稳定。
- 如果 re-run CI 后仍失败，建议在同一 CI 节点上手工执行 `curl -v` 测试该仓库的 HTTP/2 连接状态，以确认是否为节点到仓库之间的网络路径问题。
