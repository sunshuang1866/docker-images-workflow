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
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库镜像在构建期间持续返回 HTTP/2 流协议错误（Curl error 92），dnf 多次切换镜像重试后所有镜像均失败，导致 `gcc`、`gcc-gfortran`、`guile`、`glibc-devel` 等多个包无法下载，构建中的 builder 阶段（#8）和 stage-1 阶段（#7）均受影响。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 唯一的功能性变更是新增一个 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`），该 Dockerfile 语法正确、`dnf install` 命令格式无误。失败的直接原因是 openEuler 24.03-LTS-SP4 的官方 RPM 仓库在 CI 构建时间窗口（2026-07-09 14:47 UTC 附近）内，其 HTTP/2 服务端存在协议实现问题，导致 dnf/curl 客户端在下载 RPM 包时遭遇 `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`。重试到所有可用镜像均耗尽后仍未成功。

## 修复方向

### 方向 1（置信度: 高）
**无须代码修改。** 此失败属于 openEuler 24.03-LTS-SP4 RPM 仓库的临时性基础设施问题（HTTP/2 服务端协议错误），待仓库管理员修复 HTTP/2 服务端后，重新触发 CI 构建即可通过。Code Fixer 无需处理。

### 方向 2（置信度: 低）
若仓库 HTTP/2 问题持续存在，可考虑在 Dockerfile 的 `dnf install` 命令前添加 `dnf config-manager` 配置将仓库协议降级到 HTTP/1.1，或添加 `--setopt=minrate=0 --setopt=timeout=120` 等重试参数。但这是绕过上游基础设施缺陷的临时方案，不建议作为正式修复。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 仓库 `repo.****.org` 的 HTTP/2 服务在当前时间是否已恢复正常。
- 确认该仓库是否有已知的 HTTP/2 协议兼容性问题（特定版本的 nginx/haproxy/CDN 前端可能对某些 curl/libcurl 版本的 HTTP/2 实现存在兼容性缺陷）。
- 确认同仓库其他使用 `openEuler 24.03-lts-sp4` 基础镜像的 Dockerfile（如 `Others/wireshark/4.6.5`，PR #2938）最近是否也出现类似的 dnf 下载失败 — 如果多个 PR 同时受影响，可进一步证实是上游仓库问题。
