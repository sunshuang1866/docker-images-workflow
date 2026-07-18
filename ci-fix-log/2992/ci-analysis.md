# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2传输失败
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 is NOT an internal error: [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段的 `RUN dnf install`）
- 失败原因: openEuler 24.03-LTS-SP4 官方软件仓库（`repo.****.org`）在 CI 构建期间出现 HTTP/2 传输层错误，多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载时遭遇 `Curl error (92): Stream error in the HTTP/2 framing layer`，DNF 重试全部镜像后仍然失败，导致 `dnf install` 步骤以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了一个标准 Dockerfile（安装编译依赖 → git clone → 编译 → 多阶段复制），Dockerfile 本身的 `dnf install` 命令语法完全正确。失败根因是 openEuler 24.03-LTS-SP4 软件仓库在构建时刻存在 HTTP/2 传输不稳定性，属于 CI 基础设施/远端仓库问题。runtime 阶段（#7）的 `dnf install` 也遭遇了同类 `Curl error (92)`（glibc-devel、gcc-gfortran），进一步印证这是仓库端的系统性网络问题，而非 Dockerfile 特定错误。

## 修复方向

### 方向 1（置信度: 高）
此失败为远端仓库网络问题，**Code Fixer 无需处理**。建议：
- 重新触发 CI 构建（retry），等待 openEuler 24.03-LTS-SP4 仓库恢复 HTTP/2 连接稳定性。
- 若多次重试仍失败，需联系 openEuler 镜像站运维排查仓库侧 HTTP/2 服务配置。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）在 CI 构建时段是否存在 HTTP/2 配置异常或负载过高问题。
- 同一时段其他 openEuler 24.03-LTS-SP4 镜像的 CI 构建是否也出现了相同的 `Curl error (92)` 失败，以确认是否为仓库级故障而非本 PR 孤立事件。
