# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败原因: `repo.openeuler.org` 镜像站在 HTTP/2 协议层面发生多次 `INTERNAL_ERROR` 流重置（Curl error 92），导致多个 RPM 包（git-core、gcc-c++、guile）下载中断。其中 git-core 和 gcc-c++ 在重试后下载成功，但 `guile` 包在耗尽所有镜像重试后仍无法完成下载，`dnf install` 最终失败。

### 与 PR 变更的关联
**无关。** PR 的变更内容为新增 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`（13 行，标准的 `dnf install` + `git clone` + `cmake` 构建流程），以及配套的 README、image-info.yml、meta.yml 文档更新。Dockerfile 本身的语法和构建逻辑完全正确（`dnf install -y git gcc gcc-c++ make cmake` 是合法命令，且与同项目的 vvenc 24.03-lts-sp3 Dockerfile 结构一致）。失败发生在构建基础设施层——openEuler 官方镜像仓库在 aarch64 构建节点上的 HTTP/2 连接不稳定，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**触发 CI 重试。** 该失败是 openEuler 镜像仓库 `repo.openeuler.org` 在特定时段的 HTTP/2 服务不稳定导致的瞬时网络错误。多次重试（git-core、gcc-c++ 均重试成功）表明镜像站本身可访问，只是间歇性出现 HTTP/2 流重置。重新触发 CI 构建大概率可通过。

### 方向 2（置信度: 中）
如果重试多次仍然失败，可在 Dockerfile 的 `dnf install` 命令中添加 `--setopt=retries=10` 参数，增加 dnf 对单个包的重试次数（当前默认值可能不足以应对间歇性 HTTP/2 中断）。但这不是必需的代码修复——优先尝试重试 CI。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 HTTP/2 服务在此时间段是否存在已知故障
- 确认同一 PR 在 x86_64 架构节点的构建结果（日志中仅包含 aarch64 节点日志，runner 为 `ecs-build-docker-aarch64-04-sp`），若 x86_64 也失败则镜像站问题范围更大
- 确认 `guile` 包在该 aarch64 镜像源中的实际可用性（虽然错误是 HTTP/2 流错误而非 404，但排除包本身不存在的情况）
