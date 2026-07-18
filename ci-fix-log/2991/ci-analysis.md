# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
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
- 失败原因: aarch64 构建节点在 `dnf install` 过程中，从 `repo.openeuler.org` 下载 RPM 包时遭遇 HTTP/2 流层错误（Curl error 92: INTERNAL_ERROR），多个包（git-core、gcc-c++、guile）下载失败，guile 包重试所有镜像后仍失败，导致整个 `dnf install` 命令以退出码 1 失败。这是 CI 基础设施端的网络/仓库服务问题。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增的 Dockerfile 第 6 行 `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 本身语法正确、依赖声明完整，未包含任何可能导致下载失败的错误配置。失败原因纯粹是 `repo.openeuler.org` 的 aarch64 仓库在构建时刻出现了 HTTP/2 协议层面的服务端异常（内部流错误），属于基础设施/网络的临时性问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，重试 CI 即可。** 该失败为 `repo.openeuler.org` 仓库在 aarch64 构建时刻的 HTTP/2 服务端瞬时故障。Code Fixer 无需处理，等待基础设施恢复后重新触发 CI 构建（如 PR 评论区触发 `/retest` 或手动重跑）。

### 方向 2（置信度: 低）
如果该仓库的 HTTP/2 问题持续反复出现，可在 Dockerfile 的 `dnf install` 命令前添加 dnf 重试配置（如设置 `retries=10` 或 `timeout=120` 等 dnf.conf 参数）以增强网络容错能力，或强制 dnf/curl 使用 HTTP/1.1 降级下载。但这属于规避措施，非根因修复。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 aarch64 仓库是否有已知的服务端 HTTP/2 协议问题或 CDN 节点异常。
- 确认同一时段其他 PR 的 aarch64 构建是否也出现相同的 `Curl error (92): Stream error in the HTTP/2 framing layer` 错误，以确认是否为仓库侧的系统性问题。
- 确认 x86_64 架构的同 PR 构建是否也失败（日志中仅包含 aarch64 构建，无法判断 x86_64 是否成功）。
