# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, MIRROR, No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success

ERROR: failed to solve: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`
- 失败原因: openEuler 24.03-LTS-SP4 软件包仓库在 Docker 构建期间出现 HTTP/2 流错误，导致多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc 等）下载失败。`gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 在所有镜像重试后仍无法下载，`dnf install` 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关**。该失败是 CI 基础设施问题——openEuler 软件源仓库在构建期间出现 HTTP/2 连接不稳定性。PR 仅新增了一个标准格式的 Dockerfile，其 `dnf install` 命令语法和包列表均正确。日志中 stage-1（运行时阶段 #7）也出现了相同的 `Curl error (92)` 问题（`glibc-devel`、`gcc-gfortran` 包下载），进一步印证这是仓库侧问题而非 Dockerfile 错误。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。这是 openEuler 软件包仓库镜像的临时 HTTP/2 流中断问题。建议重新触发 CI 构建重试，通常此类问题为临时的网络/服务端波动，重试后很可能通过。如果持续复现，需要联系 openEuler 基础设施团队排查仓库端 HTTP/2 服务稳定性。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库 `repo.****.org` 在 CI 构建时段是否存在已知的网络/服务中断
- 如果重新触发 CI 后仍然失败，需排查是否是 CI runner 与仓库之间的 HTTP/2 协议兼容性问题（可能与 curl/libcurl 版本有关）
