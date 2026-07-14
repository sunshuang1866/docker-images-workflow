# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2流错误
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
- 失败原因: 在 aarch64 runner 上执行 `dnf install` 时，`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 仓库多个 RPM 包（git-core、gcc-c++、guile）下载过程中遭遇 HTTP/2 流错误（Curl error 92：`INTERNAL_ERROR`）。其中 git-core 和 gcc-c++ 经 DNF 自动重试后下载成功，但 guile 包耗尽所有可用镜像后彻底失败，导致整个 `dnf install` 命令退出码为 1。

## 与 PR 变更的关联

**无关**。本次 PR 仅新增了 vvenc 1.14.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据（README.md、image-info.yml、meta.yml），共 4 个文件、18 行新增。Dockerfile 中的 `dnf install` 命令语法和包列表均正确（与同项目其他 Dockerfile 一致）。失败根因是 `repo.openeuler.org` 镜像源在构建时刻的 HTTP/2 服务端流异常，属于临时的基础设施网络问题，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，触发重试即可。** 该失败是 openEuler 官方镜像源 `repo.openeuler.org` 的 HTTP/2 服务器临时故障导致的 RPM 包下载中断。属于 CI 基础设施瞬态故障，：
- 在 CI 界面触发 **重新构建（Replay/Rebuild）** 即可，绝大多数情况下仓库源恢复正常后构建可顺利通过。
- 如果多次重试仍然失败，需联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 aarch64 仓库 HTTP/2 服务稳定性。

## 需要进一步确认的点

- 确认 `repo.openeuler.org` 在构建时段（约 2026-07-09 14:09 UTC）是否存在已知的 HTTP/2 服务异常。
- 确认其他同时段提交的 openEuler 24.03-LTS-SP4 aarch64 构建（若有）是否出现同类 `Curl error (92)` 失败，以佐证其为系统性基础设施问题。
