# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org

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
- 失败原因: openEuler 24.03-LTS-SP4 的官方 yum 源 `repo.openeuler.org` 在 aarch64 架构构建过程中出现 HTTP/2 流传输错误（Curl error 92），多个 RPM 包（git-core、gcc-c++、guile）下载时 HTTP/2 连接被服务器端异常关闭（`INTERNAL_ERROR`），其中 `guile-5:2.2.7-6.oe2403sp4.aarch64` 在重试耗尽所有镜像后下载失败，导致 `dnf install` 整体返回错误码 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准 Dockerfile，其 `dnf install` 命令安装的是构建 vvenc 的基础工具链（git、gcc、gcc-c++、make、cmake），均为 openEuler 24.03-LTS-SP4 官方仓库中的常规软件包，不存在包名错误或版本冲突。失败完全由 `repo.openeuler.org` 镜像站在构建时刻的 HTTP/2 连接不稳定导致，属于 CI 基础设施层面的网络故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 此类网络层面错误通常是临时的，建议触发 CI 重试（re-run）。若问题持续出现，需由 CI 基础设施运维排查 `repo.openeuler.org` CDN/负载均衡器的 HTTP/2 配置（如检查是否有流控策略导致 `INTERNAL_ERROR`），或为 aarch64 构建节点配置备用 yum 镜像源。

### 方向 2（置信度: 中）
若长期无法解决 HTTP/2 问题，可在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制 dnf 回退到 HTTP/1.1，绕过 HTTP/2 framing layer 错误。但此为临时绕过方案，不推荐作为长期修复。

## 需要进一步确认的点
- 该 `Curl error (92)` 是否为 `repo.openeuler.org` 的已知间歇性问题，还是在特定时间段持续发生。
- `git-core` 和 `gcc-c++` 尽管报了 `[MIRROR]` 错误但最终重试下载成功（在日志后续行中有成功的进度），而 `guile` 失败——需确认 dnf 的 mirror 重试策略是否足够（当前重试次数是否偏少）。
- 构建节点 `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络路径是否存在特定问题（如中间 CDN 节点异常）。
