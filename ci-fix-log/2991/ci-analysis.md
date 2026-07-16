# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, [MIRROR], [FAILED], INTERNAL_ERROR

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: CI 在 aarch64 runner 上构建时，`repo.openeuler.org` 镜像站在提供 aarch64 RPM 包下载过程中出现 HTTP/2 流错误（Curl error 92），多个包（git-core、gcc-c++、guile）的下载流被服务端异常关闭。其中 `git-core` 通过重试成功下载，但 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 在所有镜像重试后仍失败，导致 dnf 安装步骤整体退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 变更仅为新增 vvenc 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据（README、image-info.yml、meta.yml），Dockerfile 中的 `dnf install` 命令语法完全正确。失败根因是 openEuler 官方镜像站 `repo.openeuler.org` 在 CI 构建时段出现了 aarch64 仓库的 HTTP/2 服务端流异常，属于基础设施层面的瞬时故障。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 这是典型的网络/镜像站瞬时故障（infra-error），与 PR 代码无关。等待 `repo.openeuler.org` 镜像站恢复后重新触发 CI 构建即可通过。无需修改任何代码。

### 方向 2（置信度: 低）
若多次重试后 aarch64 构建仍因同一镜像站持续不可用而失败，可考虑在 Dockerfile 的 `dnf install` 步骤前添加 `--retries` 参数或配置备用镜像源，但这属于规避措施，非根因修复。

## 需要进一步确认的点
- `repo.openeuler.org` 镜像站在 CI 构建时段（2026-07-09 14:09 UTC 前后）的 aarch64 仓库是否存在已知的 HTTP/2 服务端问题或维护窗口。
- 同一时段其他 PR 的 aarch64 构建是否也出现了相同错误（确认是否为镜像站全局性故障）。
- `guile` 作为 `git` 的传递依赖（由 perl-Git → perl → ... 引入），若希望降低对 guile 包的依赖链，可确认是否可以通过 `dnf install --setopt=install_weak_deps=False` 减少弱依赖安装范围，但这与本次失败无关。
