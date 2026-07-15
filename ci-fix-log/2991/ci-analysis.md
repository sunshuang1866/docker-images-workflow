# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, No more mirrors to try

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 仓库中的 RPM 包时，多次遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），最终因 `guile`、`gcc-c++` 等多个包无法完成下载而失败

### 与 PR 变更的关联
**无关。** 本次 PR 仅新增 vvenc 在 openEuler 24.03-LTS-SP4 平台上的 Dockerfile 及配套元数据文件，Dockerfile 中的 `dnf install` 命令为标准合法写法。失败完全由 `repo.openeuler.org` 仓库在 aarch64 架构上的 HTTP/2 协议层异常导致，属 CI 基础设施层面的网络问题，与 PR 代码改动无任何因果关系。

## 修复方向

### 方向 1（置信度: 中）
触发 CI 重试。该失败是由 openEuler 官方仓库 `repo.openeuler.org` 的 aarch64 频道在构建时段出现的 HTTP/2 协议层异常（stream INTERNAL_ERROR）导致，为间歇性网络基础设施故障。仓库恢复正常后重新触发 CI 流水线即可通过。

### 方向 2（置信度: 低）
若重试后持续复现，可考虑在 Dockerfile 的 `dnf` 命令中禁用 HTTP/2（在基础镜像中配置 DNF 使用 HTTP/1.1），或添加 `--setopt=retries=10` 提高下载重试次数以增强对网络波动的容忍度。但需注意这仅是规避手段，根因在于源仓库的 HTTP/2 服务稳定性。

## 需要进一步确认的点
- `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库在构建时段（2026-07-09 14:09 UTC）是否确实存在 HTTP/2 服务端异常
- 同一时段 x86_64 架构的 vvenc SP4 构建是否也失败（日志仅提供 aarch64 构建日志）
- 其他 new Dockerfile 在 SP4 平台的 aarch64 构建是否遇到相同问题，以判断这是单次偶发还是系统性频发
