# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: `dnf install` 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 aarch64 RPM 包时，多个包（git-core、gcc-c++、guile）遭遇 Curl error (92) — HTTP/2 传输层流错误（`INTERNAL_ERROR`），所有镜像重试均耗尽后，guile 包下载失败导致整个 `dnf install` 命令退出。

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 仅新增了 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中第 6 行的 `dnf install -y git gcc gcc-c++ make cmake` 是标准构建依赖安装步骤，语法和包的声明均无问题。

失败的直接原因是 `repo.openeuler.org` 镜像站在 CI 运行时段（2026-07-09）对 aarch64 架构的 SP4 仓库出现了 HTTP/2 协议层服务端异常，导致 rpm 包传输中断。这是一个 CI 基础设施/上游仓库稳定性问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修复。** 这是 `repo.openeuler.org` 上游仓库的临时性网络/服务端问题（HTTP/2 流内部错误），与 PR 代码变更完全无关。建议重新触发 CI 构建（rerun），待上游仓库恢复后构建应能通过。

### 方向 2（置信度: 低）
如果该仓库反复出现 HTTP/2 流错误，可考虑在 Dockerfile 的 `dnf install` 命令前添加重试逻辑（如 `dnf install -y ... || dnf install -y ...`），但这不是根本解决方案，不推荐。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 2026-07-09 期间是否出现过服务端异常或维护事件。
- 确认 aarch64 架构下 openEuler 24.03-LTS-SP4 仓库的 HTTP/2 配置是否稳定（x86_64 架构可能不受影响）。
- 日志中同时有 `git-core`、`gcc-c++`（两次失败）、`guile` 三个包遭遇 HTTP/2 流错误，说明这不是某个特定包的偶发问题，而是服务端普遍性地返回了 HTTP/2 协议层错误。
