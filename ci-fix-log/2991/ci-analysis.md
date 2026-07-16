# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, repo.openeuler.org, dnf install

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
- 失败原因: CI 在 aarch64 runner 上构建时，`dnf install` 从 `repo.openeuler.org` 下载 RPM 包（git-core、gcc-c++、guile 等）过程中遭遇 HTTP/2 流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`），多个包反复重试均失败，最终 `guile` 耗尽所有镜像源后安装失败。此错误与 PR 代码变更无关，属于 `repo.openeuler.org` 仓库源的网络/协议层基础设施问题。

### 与 PR 变更的关联
**与 PR 无关。** PR #2991 的变更仅为新增 vvenc 1.14.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中 `dnf install -y git gcc gcc-c++ make cmake` 命令标准且正确。失败发生在 dnf 从 `repo.openeuler.org` 下载依赖包的阶段，是远端仓库 HTTP/2 服务端异常导致的纯基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 此失败为 `repo.openeuler.org` 仓库源 HTTP/2 传输层临时故障。重新触发 CI 构建（retry）即可，待仓库服务器侧 HTTP/2 服务恢复正常后构建应能通过。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段是否存在已知的 HTTP/2 或负载均衡服务异常（可联系 openEuler 基础设施团队确认）。
- 观察后续其他 openEuler 24.03-LTS-SP4 相关 PR 是否也出现同类 `Curl error (92)` 错误，以判断是偶发波动还是系统性故障。
- 本 PR 仅出现在 aarch64 runner 上的构建日志，x86_64 架构的构建 job 日志未提供，若有需要可对比确认是否仅 aarch64 仓库源受影响。
