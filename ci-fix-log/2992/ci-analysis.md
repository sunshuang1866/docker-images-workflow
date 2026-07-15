# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try

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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`（builder 阶段 `dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库服务器在执行 HTTP/2 下载时反复出现 `Stream error in the HTTP/2 framing layer`（Curl error 92），多个 RPM 包（`gcc`、`gcc-gfortran`、`glibc-devel`、`guile`）均受影响，经过多次 mirror 重试后 `gcc` 包最终耗尽所有镜像源，dnf 下载失败导致构建中断。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个合法的 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`），其 `dnf install` 命令语法正确，所需包名均有效。失败原因是 openEuler 24.03-LTS-SP4 上游 RPM 仓库的 HTTP/2 服务端存在协议层问题，同一日志中 builder 阶段（#8）和 runtime 阶段（#7）的 dnf 进程均遭遇了相同的 HTTP/2 stream 错误，且部分包在重试后成功下载（#7 的 `glibc-devel` 在第一次 mirror 错误后于 `#7 1374.9` 重试成功），说明这是 repo 服务端的间歇性问题，与 Dockerfile 内容无关。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 这是上游 RPM 仓库的 HTTP/2 服务端间歇性故障，不属于代码问题。等待仓库服务恢复后重新触发构建流水线即可。如果问题持续，可联系 openEuler 基础设施团队排查 repo 服务器的 HTTP/2 配置或负载情况。

### 方向 2（置信度: 中）
**如果问题持续出现，可在 Dockerfile 的 dnf 配置中添加重试/超时参数。** 在 `dnf install` 前设置 `echo "retries=10" >> /etc/dnf/dnf.conf` 和 `echo "timeout=120" >> /etc/dnf/dnf.conf` 增加 dnf 自身的下载重试次数与超时容忍度，提高对间歇性 HTTP/2 错误的容错能力。但此方向仅为临时缓解措施，根本解决仍需上游仓库修复。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 RPM 仓库的 HTTP/2 服务端是否已恢复正常（可在 CI 环境中单独执行 `dnf download gcc-12.3.1-110.oe2403sp4 --repo=OS` 验证）
- 确认同一时段是否有其他 PR（同样基于 24.03-lts-sp4）也遭遇相同错误，以排除本 PR 的 Dockerfile 中包名或仓库配置存在特殊问题

## 修复验证要求
无需修复验证。此报告判定为 infra-error，Code Fixer 无需处理。
