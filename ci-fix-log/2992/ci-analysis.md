# CI 失败分析报告

## 基本信息
- PR: #2992 — chore(multiwfn): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2协议错误
- 新模式症状关键词: `Curl error (92)`, `Stream error in the HTTP/2 framing layer`, `INTERNAL_ERROR (err 2)`, `[MIRROR]`, `[FAILED]`, `No more mirrors to try`, `Error downloading packages`

## 根因分析

### 直接错误
```
#8 1243.9 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 31 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1468.3 [MIRROR] gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-gfortran-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 37 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1767.8 [MIRROR] guile-2.2.7-6.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/guile-2.2.7-6.oe2403sp4.x86_64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.****.org/openEuler-24.03-LTS-SP4/OS/x86_64/Packages/gcc-12.3.1-110.oe2403sp4.x86_64.rpm [HTTP/2 stream 27 was not closed cleanly: INTERNAL_ERROR (err 2)]
#8 1830.2 [FAILED] gcc-12.3.1-110.oe2403sp4.x86_64.rpm: No more mirrors to try - All mirrors were already tried without success
#8 1830.2 Error: Error downloading packages:
#8 1830.2   gcc-12.3.1-110.oe2403sp4.x86_64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile:7-10`（`dnf install` 步骤，builder 阶段）
- 失败原因: openEuler 24.03-LTS-SP4 软件仓库镜像（`repo.****.org`）在 HTTP/2 传输过程中频繁发生 `INTERNAL_ERROR` 流中断（curl error 92），多个 RPM 包（gcc-gfortran、glibc-devel、guile、gcc）下载均受波及，其中 `gcc-12.3.1-110.oe2403sp4.x86_64.rpm`（34 MB）最终耗尽所有镜像重试后失败，导致 `dnf install` 以 exit code 1 退出。同时期运行的 stage-1（#7）也出现同类镜像错误（glibc-devel、gcc-gfortran），在 builder 阶段失败后被取消。

### 与 PR 变更的关联
**无关。** PR 仅新增了 Multiwfn 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），均为标准的前端声明性文件。Dockerfile 中的 `dnf install` 命令语法正确、依赖列表合理。失败完全由 openEuler 软件仓库镜像的 HTTP/2 协议层瞬时故障引起，是 CI 基础设施问题，与 PR 代码变更无因果关系。

## 修复方向

### 方向 1（置信度: 高）
**无需修复 PR 代码，直接重试 CI。** 该失败为 openEuler 24.03-LTS-SP4 软件仓库镜像的临时性 HTTP/2 协议错误，属于基础设施层面的间歇性故障。对同一个 PR 重新触发 CI 构建即可（Jenkins 中 "Rebuild" 或在 PR 上新增空 commit 触发重新构建）。若重试后仍失败，需联系仓库镜像运维排查 HTTP/2 服务器端问题。

## 需要进一步确认的点
- 无。日志已充分证明失败源于镜像站 HTTP/2 协议错误（curl error 92），该错误在多包下载过程中反复出现，与任何 PR 代码逻辑无关。

## 修复验证要求
不适用。本失败为 infra-error，无需对代码做任何修改。验证方式：重新触发 CI，若同一 job 在软件仓库正常时通过即确认根因正确。
