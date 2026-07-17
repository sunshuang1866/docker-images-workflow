# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7`
- 失败原因: openEuler 24.03-LTS-SP4 官方软件源（`repo.****.org`）的 HTTP/2 传输层频繁报 `INTERNAL_ERROR (err 2)`，导致 dnf 下载多个 RPM 包（`gcc`、`gcc-gfortran`、`glibc-devel`、`guile`）时 Curl 报错（error code 92），重试耗尽所有镜像后失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增 multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套 README/meta 更新，Dockerfile 语法和构建逻辑本身正确。失败原因是 CI 构建环境中 openEuler 24.03-LTS-SP4 的软件仓库镜像站 HTTP/2 服务端存在协议层缺陷（`Stream error in the HTTP/2 framing layer`），导致 dnf 无法正常下载 GCC、glibc-devel 等编译工具链 RPM 包。两个构建阶段（`#7` runtime 阶段、`#8` builder 阶段）均受镜像源抖动影响。

## 修复方向

### 方向 1（置信度: 低）
等待 openEuler 24.03-LTS-SP4 软件源镜像站恢复。HTTP/2 `INTERNAL_ERROR` 是服务端协议层错误，客户端（dnf/curl）无法规避。当镜像站服务恢复后，重新触发 CI 即可通过。

### 方向 2（置信度: 低）
若镜像站问题持续，可在 Dockerfile 的 dnf 命令前添加重试/降级策略，例如：
- 配置 dnf 使用 HTTP/1.1 而非 HTTP/2（`dnf install --setopt=protocol=1.1 ...`）以规避 HTTP/2 服务端缺陷
- 切换至备选镜像站（如 `repo.huaweicloud.com`）作为 dnf 仓库源

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 官方软件源 `repo.****.org` 的 HTTP/2 服务是否已恢复正常
- CI 环境中 dnf 是否有可配置的备选镜像站列表
- 是否有其他 openEuler 24.03-LTS-SP4 的 PR 构建在相同时间段也遇到了同一问题（以确认是否为临时性基础设施故障）
