# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1268.5 [MIRROR] glibc-devel-2.38-107.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/glibc-devel-2.38-107.oe2403sp4.x86_64.rpm [HTTP/2 stream 17 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 15 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]

#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install -y git gcc gcc-c++ gcc-gfortran make openblas-devel lapack-devel` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 仓库镜像服务器在处理 HTTP/2 请求时返回 `INTERNAL_ERROR`（Curl error 92），导致多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载中途失败。其中 `gcc` 包（34 MB）在多次重试到所有镜像后仍然失败，触发 `No more mirrors to try` 致命错误。Dockerfile 中新 `builder` 阶段的 `dnf install` 步骤因此 exit code 1，且 `stage-1` 的并行 `dnf install` 被随之取消。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2992 的变更仅包含：
- 新增 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`），内容为纯声明式包安装和编译指令
- README.md 新增一行表格条目
- image-info.yml 新增一行表格条目
- meta.yml 新增一个 tag → path 映射

这些变更不涉及任何网络配置、仓库源修改或可导致 HTTP/2 协议错误的代码。失败根因是 openEuler 24.03-LTS-SP4 仓库镜像服务器端的 HTTP/2 流异常（`INTERNAL_ERROR`），属于 CI 基础设施问题。即使同分支中已有的 `stage-1` 阶段（安装更少的包）也受到了同样的 HTTP/2 流错误影响（`glibc-devel`、`gcc-gfortran` 均出现 Mirror 错误），进一步证明这是仓库端问题而非 Dockerfile 问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，应重试 CI。** 这是 openEuler 24.03-LTS-SP4 仓库镜像服务器的瞬时 HTTP/2 协议故障，属于 CI 基础设施问题。Code Fixer Agent 无需处理。建议在镜像仓库服务恢复正常后重新触发 CI 构建（re-run / re-trigger the pipeline）。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在 CI 构建时间点（2026-07-09 14:46~14:58 UTC）是否存在已知的 HTTP/2 服务端问题或维护窗口
- 同期其他使用同一基础镜像（`openeuler/openeuler:24.03-lts-sp4`）的 PR 是否也出现同类 `Curl error (92)` 失败，若是则可确认是仓库侧全局问题
