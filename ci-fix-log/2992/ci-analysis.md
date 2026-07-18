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
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ... [HTTP/2 stream 37 ... INTERNAL_ERROR (err 2)]
#7 1598.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error ... [HTTP/2 stream 15 ... INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error ... [HTTP/2 stream 43 ... INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error ... [HTTP/2 stream 27 ... INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
------ 
Dockerfile:7
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（builder 阶段 `dnf install` 步骤）
- 失败原因: CI 构建环境中，openEuler 24.03-LTS-SP4 仓库镜像在多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载过程中反复出现 HTTP/2 协议层流错误（Curl error 92），最终 `gcc` 包的下载耗尽了所有可用镜像重试次数，导致 `dnf install` 失败。该错误与 Dockerfile 构建逻辑或 PR 代码变更无关，属于仓库侧网络基础设施问题。

### 与 PR 变更的关联
无关。PR #2992 仅为 multiwfn 新增了 openEuler 24.03-LTS-SP4 的 Dockerfile 及配套元数据（README.md、image-info.yml、meta.yml），变更内容仅涉及 Dockerfile 编写与文档更新。构建失败发生在 `dnf install` 从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包的阶段，所有错误均为 `Curl error (92): Stream error in the HTTP/2 framing layer`，属于仓库镜像/网络层故障，与 PR 的 Dockerfile 本身或构建逻辑无关。同时，stage-1（`#7`）在下载同类包时也遇到了相同的 HTTP/2 流错误（`glibc-devel`、`gcc-gfortran`），进一步证实该问题是该仓库镜像在本次构建时间段的系统性问题。

## 修复方向

### 方向 1（置信度: 高）
无需修改代码。该失败属于 `infra-error`，由 openEuler 24.03-LTS-SP4 软件仓库镜像在 CI 构建时段的 HTTP/2 协议层不稳定导致。应触发 CI 重新运行（retry），等待仓库镜像恢复稳定后构建大概率可通过。若重试仍持续失败，需联系 openEuler 镜像站运维排查 repo.****.org 的 HTTP/2 服务状态。

## 需要进一步确认的点
- 同一时间段内其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也出现类似 `Curl error (92)` 报错——若多 PR 同时出现，可确认是仓库侧基础设施问题。
- 该仓库镜像站（`repo.****.org`）的 HTTP/2 服务是否存在已知的间歇性故障或限流策略。
