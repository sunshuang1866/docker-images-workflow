# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, MIRROR, dnf install, repo.openeuler.org

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
- 失败位置: Dockerfile:6 — `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`
- 失败原因: CI aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）与 `repo.openeuler.org` 之间的 HTTP/2 连接出现流层错误（`INTERNAL_ERROR (err 2)`），导致多个 aarch64 RPM 包下载失败。其中 `git-core` 和 `gcc-c++` 经镜像重试后成功下载，但 `guile-5:2.2.7-6.oe2403sp4.aarch64` 在所有镜像均重试失败后无可用源，dnf 安装中止。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准的 vvenc 1.14.0 Dockerfile（安装构建依赖 → git clone → cmake 构建）以及配套的 README、image-info.yml、meta.yml 元数据更新。Dockerfile 中 `dnf install` 安装的包名均为 openEuler 24.03-LTS-SP4 仓库的有效包（日志中依赖解析成功，列出了 156 个待安装包），失败完全由 CI 构建节点与 repo.openeuler.org 之间的网络/HTTP 传输问题导致。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施问题，Code Fixer 无需处理。** 失败原因为 aarch64 构建节点下载 openEuler RPM 包时发生的 HTTP/2 流传输错误，属于临时性网络基础设施故障。建议在 CI 侧重试该 job（re-trigger build），观察是否复现。

### 方向 2（置信度: 低）
如果该问题在多轮重试后持续复现，可能需要排查 `repo.openeuler.org` 的 aarch64 镜像站 HTTP/2 配置是否存在问题，或考虑在 Dockerfile 中将 dnf 安装拆分为多次小批量安装以降低单次下载失败的影响范围。但此方向属于平台侧修复，非 PR 代码层面可解决。

## 需要进一步确认的点
- 在 aarch64 runner 上重新触发本次构建（re-run CI），确认是否为一次性网络抖动还是持续性基础设施问题。
- 如果持续复现，需排查 `repo.openeuler.org` aarch64 镜像源的 HTTP/2 服务端配置（如 `INTERNAL_ERROR` 是否为服务端的特定限流或协议兼容性问题）。
