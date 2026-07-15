# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install, repo.openeuler.org, aarch64

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在执行 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），最终 `guile` 包在所有镜像重试后仍无法下载，导致 dnf 安装失败。这是 CI 构建环境与 openEuler 官方仓库之间的网络/协议层问题，与 PR 代码变更无关。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 仅新增了 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件，Dockerfile 中 `dnf install -y git gcc gcc-c++ make cmake` 命令语法正确、包名有效。失败纯粹是由 CI 构建节点的 aarch64 runner 连接 `repo.openeuler.org` 时发生 HTTP/2 协议层传输错误导致的。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。此错误属于临时性基础设施/网络问题（HTTP/2 stream INTERNAL_ERROR），通常由镜像站瞬时不稳定或 CI runner 与仓库之间的网络波动引起。直接在 Jenkins 中重新触发 CI 构建，大概率可以通过。

### 方向 2（置信度: 低）
如果多次重试仍然失败，可以考虑在 Dockerfile 中将 dnf 仓库协议从 HTTP/2 降级为 HTTP/1.1（在 `dnf install` 前设置 `echo "http2=false" >> /etc/dnf/dnf.conf` 或在 curl 层面禁用 HTTP/2）。但不建议作为首选方案，因为 HTTP/2 流错误通常是暂时的，且降级协议会影响下载性能。

## 需要进一步确认的点
- x86_64 架构的 CI 构建是否也失败了（日志仅显示了 aarch64 runner 的构建），如果 x86_64 也失败，可能是 `repo.openeuler.org` 仓库整体故障而非单架构问题。
- aarch64 runner 是否在后续构建中持续出现同类 `Curl error (92)` 错误，以判断是 runner 节点问题还是上游仓库问题。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
无需填写（本次为 infra-error，不涉及代码修复）。
