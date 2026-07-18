# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库 HTTP/2 不稳定
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, MIRROR, aarch64

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
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `dnf install` 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 aarch64 RPM 包时，多个包（`git-core`、`gcc-c++`、`guile`）遭遇 HTTP/2 流层错误（Curl error 92: INTERNAL_ERROR）。其中 `git-core` 和 `gcc-c++` 在重试后成功下载，但 `guile` 耗尽所有镜像重试后仍失败（`No more mirrors to try`），导致整个 `dnf install` 命令以退出码 1 失败。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了一个标准的 vvenc Dockerfile（`dnf install -y git gcc gcc-c++ make cmake && dnf clean all`），构建指令本身完全正确。失败原因是 CI 构建环境中 `repo.openeuler.org` 的 aarch64 CDN 节点在构建窗口期内出现 HTTP/2 连接不稳定，属于基础设施层面的网络故障。

## 修复方向

### 方向 1（置信度: 高）
纯基础设施故障，无需修改任何代码或 Dockerfile。应重新触发 CI 构建（retry），待 `repo.openeuler.org` 的 aarch64 节点网络恢复稳定后构建即可通过。该问题与 PR #2991 的代码变更完全无关。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 CDN 节点是否存在已知的 HTTP/2 稳定性问题
- 若频繁复现此类错误，可考虑在 CI 构建脚本中增加 `dnf install` 的重试机制（如 `dnf install -y --setopt=retries=10 ...`）或降级使用 HTTP/1.1 协议
