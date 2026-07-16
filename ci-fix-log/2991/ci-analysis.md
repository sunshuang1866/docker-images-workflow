# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 构建在 aarch64 节点（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，`repo.openeuler.org` 服务端的 HTTP/2 连接频繁被服务端以 `INTERNAL_ERROR` 异常关闭（Curl error 92），导致多个软件包（git-core、gcc-c++、guile）下载失败。其中 `guile` 包耗尽所有重试次数后彻底失败，整个 `dnf install` 命令退出码为 1，触发了 Docker 构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`）及配套的文档/元数据更新（README.md、image-info.yml、meta.yml）。失败发生在 `dnf install` 阶段——即 Docker 构建的第一个 RUN 层（`#7 [2/3]`），尚未进入 vvenc 源码编译步骤。Dockerfile 中的 `dnf install` 命令语法完全正确，失败根因是 `repo.openeuler.org` 镜像站在该时间段对 aarch64 架构节点的 HTTP/2 服务不稳定。`git-core` 和 `gcc-c++` 包均在 DNF 自动切换镜像后重试成功，唯独 `guile` 在所有镜像源均失败后耗尽重试次数。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，重试 CI 即可。** 这是 openEuler 官方仓库 `repo.openeuler.org` 在特定时段的 HTTP/2 服务端稳定性问题，非 PR 代码引入。等待仓库服务恢复后重新触发 CI 构建大概率可以通过。

### 方向 2（置信度: 低）
如果该问题频繁复现，可在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=10` 增加重试次数，或添加 `--setopt=timeout=120` 增加超时容忍度，以应对仓库端的间歇性 HTTP/2 流错误。但这只是缓解措施，不能根本解决问题。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段是否存在服务端问题（HTTP/2 INTERNAL_ERROR 是服务端主动关闭流的错误码，通常表示服务端负载过高或后端异常）
- 确认该 aarch64 runner 节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否稳定
- 如果同时间段其他 PR 的 aarch64 构建也出现类似错误，可进一步确认是仓库端问题而非个别节点问题

## 修复验证要求
无需 code-fixer 介入。此为 infra-error，Code Fixer 无需处理。建议重新触发 CI 构建验证。
