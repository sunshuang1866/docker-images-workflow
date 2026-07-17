# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源HTTP/2协议错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR (err 2), MIRROR, dnf

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
- 失败原因: CI 在 aarch64 runner (`ecs-build-docker-aarch64-04-sp`) 上执行 `dnf install` 时，从 `repo.openeuler.org` 下载多个 RPM 包（git-core, gcc-c++, guile）遭遇 HTTP/2 流错误（Curl error 92），`guile` 包在所有重试后仍下载失败，导致 dnf 退出码 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个 Dockerfile 及相关文档/元数据更新，Dockerfile 内容完全正确（`dnf install` 命令语法无误，依赖声明完整）。失败根本原因是 openEuler aarch64 软件仓库的 HTTP/2 传输层在 CI 构建时刻出现协议错误，属于基础设施/网络层面的瞬态故障。`gcc-c++` 包曾重试一次（stream 39 失败后 stream 51 重试即成功），但 `guile` 重试耗尽后仍未成功。

## 修复方向

### 方向 1（置信度: 高）
**CI 重试即可，无需修改代码。** 这是 `repo.openeuler.org` 软件源在特定时刻的 HTTP/2 服务端异常，与 PR 代码无关。联系 CI 管理员重新触发 aarch64 构建 job 即可。若问题频繁复现，可建议 CI 运维排查 `repo.openeuler.org` 的 HTTP/2 前端（如 CDN/负载均衡器）的稳定性，或考虑在 Dockerfile 的 `dnf install` 前添加 `--retries` 参数增加重试次数（此为防御性措施，非根因修复）。

### 方向 2（置信度: 低）
若重试持续失败，需排查 `repo.openeuler.org` 对特定源 IP 或 HTTP/2 连接的限制策略（如 rate limiting 导致 stream 被服务端异常关闭）。

## 需要进一步确认的点
1. `repo.openeuler.org` 在 CI 失败时刻的 HTTP/2 服务状态（服务端日志中 stream 43/39/51/49 的 INTERNAL_ERROR 详细原因）。
2. 是否存在仅影响 aarch64 仓库路径的网络问题（本次失败的包均为 `OS/aarch64/Packages/` 下的 RPM）。
3. 同一时刻 x86_64 架构的 vvenc 构建是否也因相同原因失败（日志中仅包含 aarch64 runner 的构建日志）。
