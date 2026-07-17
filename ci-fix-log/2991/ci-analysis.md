# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2传输错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, dnf download

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: `repo.openeuler.org` 在向 aarch64 构建节点提供 RPM 包时，HTTP/2 传输层发生多次 Stream Error（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），导致 `git-core`、`gcc-c++`、`guile` 等多个包的下载被中断。其中 `guile` 包在耗尽所有镜像重试后彻底失败，`dnf install` 返回 exit code 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 只新增了一个标准的 vvenc Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`），其 `dnf install` 命令语法正确、依赖声明合理。失败完全由 openEuler 官方软件仓库 `repo.openeuler.org` 在 aarch64 架构构建期间的 HTTP/2 传输层故障引起，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 该失败为 `repo.openeuler.org` 仓库在构建时段发生的瞬时性 HTTP/2 传输层故障，与 PR 代码无关。待仓库服务恢复稳定后重试即可通过。Code Fixer 无需对 Dockerfile 做任何修改。

## 需要进一步确认的点
- 如果多次重试后仍然出现同样的 HTTP/2 错误，需要确认 `repo.openeuler.org` 的 aarch64 仓库是否存在持续性的 HTTP/2 配置问题或运维故障。
- 确认是否其他 PR 在同一时段也遭遇了相同的 `Curl error (92)` 错误——如果是，则为 openEuler 基础设施层面的系统性问题。
