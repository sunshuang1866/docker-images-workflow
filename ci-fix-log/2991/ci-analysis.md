# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, repo.openeuler.org, No more mirrors to try

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
ERROR: failed to solve: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:6（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库（`repo.openeuler.org`）在 aarch64 架构的 Docker 构建过程中，多个 RPM 包（`git-core`、`gcc-c++`、`guile`）下载时出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）。其中 `git-core` 和 `gcc-c++` 经重试后成功下载，但 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 在耗尽所有镜像源后仍下载失败，最终导致 `dnf install` 退出码为 1，Docker 构建失败。

### 与 PR 变更的关联
**与 PR 无关**。PR 变更仅新增了一个标准的 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`），其中的 `dnf install` 命令为常规的编译依赖安装（`git gcc gcc-c++ make cmake`），语法正确，包名有效。失败原因是 openEuler 官方仓库在特定时段对 aarch64 架构出现了 HTTP/2 协议层面的服务端故障（`INTERNAL_ERROR`），属于 CI 基础设施问题，非代码缺陷。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。HTTP/2 流错误（`INTERNAL_ERROR err 2`）是服务端临时性故障，下游仓库可能在不同时间段恢复正常。直接触发重新构建（rerun CI），多数情况下仓库恢复后即可通过。

### 方向 2（置信度: 低）
**规避 HTTP/2**。若该仓库的 HTTP/2 问题持续复现，可在 Dockerfile 的 `dnf install` 之前配置 dnf 强制使用 HTTP/1.1（通过 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置 libcurl 环境变量禁用 HTTP/2），以绕过仓库 HTTP/2 协议栈的服务端缺陷。此方向仅应在多次重试仍失败后采用。

## 需要进一步确认的点
- 此失败是否仅在 aarch64 架构上发生，还是 x86_64 构建也受影响？当前日志仅来自 aarch64 runner。
- `repo.openeuler.org` 的 HTTP/2 故障是否为已知的间歇性问题，是否可以联系基础设施团队确认仓库服务状态。
- 如果重试后仍然失败，需要确认是 `guile` 包本身在 SP4 仓库中缺失，还是 HTTP/2 流错误导致所有大文件下载均失败。
