# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), No more mirrors to try, dnf install

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
- 失败原因: CI 在 aarch64 runner 上执行 `dnf install` 时，`repo.openeuler.org` 仓库服务器多次出现 HTTP/2 流协议错误（`INTERNAL_ERROR (err 2)`），导致 `git-core`、`gcc-c++`、`guile` 三个 RPM 包的下载失败。其中 `guile` 包在耗尽所有镜像重试后仍未成功下载，最终 `dnf` 退出码 1，构建失败。

### 与 PR 变更的关联
无关。PR 仅新增了一个标准格式的 Dockerfile（`dnf install` → `git clone` → `cmake build`），Dockerfile 本身语法和逻辑正确。失败完全由 `repo.openeuler.org` 仓库服务器的 HTTP/2 协议层面瞬时故障导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 `repo.openeuler.org` 仓库服务器的瞬时网络故障（HTTP/2 流中断）。建议在 CI 中对该 PR 触发 **rerun / rebuild**，通常重试即可成功。若多次重试仍失败，需联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 服务端问题。

## 需要进一步确认的点
- 是否存在多个 PR 在同一时间段（2026-07-09 14:08 UTC 前后）的 aarch64 CI 构建同时失败——若存在，进一步确认是仓库服务端问题而非个别 runner 的网络问题。
- `repo.openeuler.org` 在 CI 构建时间窗口内是否存在已知的 HTTP/2 服务端异常或中断。

## 修复验证要求
不适用（infra-error，无需代码修复）。
