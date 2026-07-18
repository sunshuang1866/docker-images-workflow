# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try

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
#8 ERROR: process "/bin/sh -c dnf install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`RUN dnf install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像在 CI 构建期间出现 HTTP/2 流错误（`Curl error 92: INTERNAL_ERROR (err 2)`），多个 RPM 包（`gcc-gfortran`、`glibc-devel`、`guile`、`gcc`）下载遭遇 HTTP/2 流中断。builder 阶段（#8）的 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm` 在所有镜像重试均失败后彻底报错，导致 `dnf install` 退出码为 1。同一构建中 stage-1（#7）也遭遇了同样的镜像错误但部分包通过重试成功，最终因 builder 阶段失败被 CANCELED。

### 与 PR 变更的关联
**无关**。PR 仅新增了一个标准的 Dockerfile（使用 `dnf install` 安装构建依赖）、更新了 README.md 和 meta.yml。Dockerfile 语法正确，`dnf install` 命令格式与仓库中其他 openEuler 24.03-lts-sp4 镜像一致。失败原因是 openEuler 24.03-LTS-SP4 仓库镜像服务端的 HTTP/2 协议实现不稳定，属于 CI 基础设施 / 上游镜像站问题，与本次代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**触发重试**：无需修改代码。该失败为 openEuler 24.03-LTS-SP4 仓库镜像瞬时不稳定导致的网络问题，应在 CI 中重新触发构建（re-run）。若多次重试均失败，需联系 openEuler 基础设施团队排查 `repo.****.org` 镜像站的 HTTP/2 服务端问题。

## 需要进一步确认的点
- openEuler 24.03-LTS-SP4 仓库镜像站（`repo.****.org`）在 CI 构建时段的 HTTP/2 服务状态。可查看该时段其他 openEuler 24.03-lts-sp4 镜像的 CI 构建是否也出现同类 Curl error (92)。
- 该仓库镜像是否支持 HTTP/1.1 回退，以便在 dnf 配置中临时禁用 HTTP/2 来规避问题。
