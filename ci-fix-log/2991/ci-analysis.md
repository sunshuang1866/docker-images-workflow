# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, No more mirrors to try

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`:6（`dnf install` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`dnf install` 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 aarch64 RPM 包时，多个包遭遇 HTTP/2 流错误（Curl error 92），最终 `guile` 包（git 的传递依赖）在所有镜像重试后仍下载失败，导致构建中断。

### 与 PR 变更的关联
**与 PR 代码无关。** 该 PR 新增的 Dockerfile 内容（`dnf install -y git gcc gcc-c++ make cmake`）语法正确，是仓库中已有的标准模式。失败完全由 openEuler 官方软件仓库（`repo.openeuler.org`）在 aarch64 架构上的 HTTP/2 流不稳定导致。同一 PR 在 x86_64 runner 上可能构建成功（历史经验表明此类网络问题通常是间歇性的且可能与架构/节点相关）。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试/重跑。** 此为典型的间歇性网络/infra 问题。openEuler 仓库的 HTTP/2 服务在 aarch64 节点上出现临时性流错误，通常重试即可解决。Code Fixer 无需修改任何代码，只需建议 CI 管理员重新触发本次构建。

### 方向 2（置信度: 低）
**修改 dnf 配置禁用 HTTP/2。** 如果该问题持续复现，可在 Dockerfile 的 `dnf install` 之前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制 dnf 使用 HTTP/1.1 下载，规避 HTTP/2 流中断问题。但此为治标不治本，且性能下降明显，仅建议在多次重试均失败后作为临时方案。

## 需要进一步确认的点
- 确认同一 PR 是否在其他架构（x86_64）runner 上构建成功（本次日志仅提供了 aarch64 构建的日志）
- 确认 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库是否当时存在服务端问题（可查服务端 HTTP/2 流错误率监控）
- 确认 guile 包的大小（6.3 MB）是否导致传输中更容易触发 HTTP/2 流中断——从日志看，其他大包如 gcc（30 MB）、cmake（13 MB）已成功下载
