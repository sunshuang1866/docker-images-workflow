# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, MIRROR

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 ERROR: process "/bin/sh -c dnf install -y       git gcc gcc-c++ gcc-gfortran make       openblas-devel lapack-devel &&     dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤）
- 失败原因: CI 构建环境在通过 dnf 从 `repo.****.org` 下载 openEuler 24.03-LTS-SP4 仓库的 RPM 包时，多个包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）遭遇 HTTP/2 流错误（Curl error 92: Stream error in the HTTP/2 framing layer），最终 `gcc` 包在所有镜像源重试均失败后，触发了 "No more mirrors to try" 错误。这是一个 CI 基础设施/网络问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**无关**。PR 仅做了以下变更：
- 新增 `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`
- 更新 README.md、image-info.yml、meta.yml 新增对应的 tag 和路径映射

失败发生在 Dockerfile 第 7-10 行的 `dnf install` 步骤，该步骤的语法和包列表完全正确（与同类 Dockerfile（sp3 版本）格式一致）。失败根因是 openEuler 24.03-SP4 的 yum 仓库镜像站在本次构建期间出现 HTTP/2 流传输不稳定，导致多个 RPM 包下载中断。该问题是由镜像站服务器或中间网络导致的，不属于代码问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改**。这是一个 CI 基础设施问题（openEuler 24.03-LTS-SP4 仓库镜像服务器 HTTP/2 传输不稳定）。建议：
- 重新触发 CI 构建即可。镜像站网络波动通常是临时性的，重试大概率能通过。
- 若持续失败，需联系 openEuler 基础设施团队排查 `repo.****.org` 上 openEuler-24.03-LTS-SP4 仓库的 HTTP/2 服务状态。

## 需要进一步确认的点
- 检查 openEuler 24.03-LTS-SP4 仓库镜像站 `repo.****.org` 的 HTTP/2 服务在构建时间点（2026-07-09 14:46-14:48 UTC）是否存在可用性问题。
- 确认同一时间段的同类 openEuler 24.03-lts-sp4 镜像构建是否也遇到相同错误（若否，则可能是单次网络瞬时故障）。
