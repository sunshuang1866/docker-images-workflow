# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try, dnf

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: aarch64 构建节点从 `repo.openeuler.org` 下载 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 Curl error (92) —— HTTP/2 流层 `INTERNAL_ERROR`，属于 openEuler 官方仓库服务端的 HTTP/2 协议层瞬时故障。其中 git-core 和 gcc-c++ 通过镜像重试恢复，但 `guile` 包重试全部镜像后均失败，导致 dnf install 整体退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准 Dockerfile、README 条目、image-info 条目和 meta 条目，Dockerfile 中 `dnf install` 命令本身无任何语法或逻辑问题。失败完全由 openEuler 官方仓库 `repo.openeuler.org` 在 aarch64 架构上的 HTTP/2 服务端瞬时故障引起。同一基础镜像此前已有成功的 SP3 版本构建，SP4 版本 Dockerfile 逻辑完全一致。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 即可。** 该失败是 openEuler 官方 RPM 仓库 `repo.openeuler.org` 服务端的 HTTP/2 流层瞬时故障（`INTERNAL_ERROR`），与 PR 代码变更无关。等待仓库恢复后重新触发 CI 构建即可通过。

## 需要进一步确认的点
- 无。日志证据充分，Curl error (92) 的 HTTP/2 `INTERNAL_ERROR` 明确指向服务端问题，与 Dockerfile 内容无关。
- 建议确认 x86_64 架构的同 PR 构建是否已经成功（若 CI 同时触发多架构构建，x86_64 可能未受该仓库瞬时故障影响）。
