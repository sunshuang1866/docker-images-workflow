# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, dnf install

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
- 失败原因: aarch64 构建节点在执行 `dnf install` 时，从 `repo.openeuler.org` 下载 RPM 包过程中遭遇 HTTP/2 流错误（Curl error 92），4 个包（`git-core`、`gcc-c++` x2、`guile`）均出现 `INTERNAL_ERROR (err 2)`，其中 `guile` 在耗尽所有镜像重试后最终失败，导致整个 dnf 事务中断。

### 与 PR 变更的关联
**无关。** PR 仅新增了 vvenc 1.14.0 的 Dockerfile（标准 `dnf install` + `cmake` 构建）及配套元数据文件。`dnf install -y git gcc gcc-c++ make cmake` 命令本身正确，失败完全源于构建节点与 `repo.openeuler.org` 之间的网络传输层问题，属于 CI 基础设施故障。同一 Dockerfile 在 x86_64 runner 上很可能构建成功（但该 runner 的日志未提供）。

## 修复方向

### 方向 1（置信度: 中）
**无需修改代码，触发 CI 重试即可。** 该失败为 `repo.openeuler.org` 镜像站 HTTP/2 服务的间歇性故障，多个包（`git-core`、`gcc-c++`、`guile`）均在同一构建过程中出现流错误，表明问题在服务器端或中间网络层。重新触发 CI 构建大概率会成功。

### 方向 2（置信度: 低）
若多次重试均失败，可考虑在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=10` 增加重试次数，以应对 `repo.openeuler.org` 的 HTTP/2 不稳定性。但更建议从 CI 基础设施侧排查 aarch64 构建节点到 `repo.openeuler.org` 的网络连通性。

## 需要进一步确认的点
1. 同一 PR 的 x86_64 架构构建 job 是否成功（当前仅提供了 aarch64 job 日志）。
2. `repo.openeuler.org` 在该时间段是否有已知的 HTTP/2 服务抖动或 CDN 节点异常。
3. aarch64 构建节点 `ecs-build-docker-aarch64-04-sp` 的历史构建成功率，是否存在类似网络问题的复发模式。
