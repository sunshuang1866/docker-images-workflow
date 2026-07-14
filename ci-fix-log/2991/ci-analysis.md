# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库 HTTP/2 流错误
- 新模式症状关键词: `Curl error (92)`, `HTTP/2 framing layer`, `INTERNAL_ERROR`, `No more mirrors to try`, `Error downloading packages`, `repo.openeuler.org`

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6` — `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`
- 失败原因: CI aarch64 构建节点在执行 `dnf install` 时，从 `repo.openeuler.org` 下载 RPM 包（`git-core`、`gcc-c++`、`guile`）反复遭遇 HTTP/2 流错误（Curl error 92），`guile` 包耗尽所有镜像重试后下载失败，导致 dnf 事务中断。

### 与 PR 变更的关联
**与 PR 改动无关。** 该失败是 openEuler 官方软件源 `repo.openeuler.org` 在构建时段向 aarch64 节点提供 HTTP/2 服务时出现的瞬态网络故障。PR 新增的 Dockerfile 中 `dnf install` 命令完全正确，所请求的包（`git`、`gcc`、`gcc-c++`、`make`、`cmake`）均为 openEuler 24.03-LTS-SP4 标准仓库中的合法包。同一命令在其他构建任务中可正常执行。

## 修复方向

### 方向 1（置信度: 高）
**infra-error，Code Fixer 无需处理。** 该失败是 openEuler 镜像站的 HTTP/2 服务端瞬时异常，触发重试即可。建议直接在 CI 中重新触发该 job 的构建。

### 方向 2（置信度: 低）
如果多次重试后 `guile` 包下载仍持续失败，可能需要联系 openEuler 镜像站运维排查 `openEuler-24.03-LTS-SP4/OS/aarch64/` 下 `guile` 包的存储完整性。

## 需要进一步确认的点
1. 重试是否通过：重新触发 CI 构建后，`dnf install` 步骤是否能成功下载 `guile` 包。如果连续 3 次均失败，则可能不是瞬态网络问题，需要向 openEuler 基础设施团队报告 `guile-5:2.2.7-6.oe2403sp4.aarch64` 包在镜像站的可用性问题。
2. `git-core` 和 `gcc-c++` 虽然报过 `[MIRROR]` 警告但最终重试成功下载（日志中未见其 `[FAILED]`），说明镜像站的重试机制部分有效，仅 `guile` 耗尽所有重试。
