# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2下载失败
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install, repo.openeuler.org

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake`）
- 失败原因: openEuler 24.03-LTS-SP4 的 RPM 仓库 `repo.openeuler.org` 在 aarch64 构建节点上返回 HTTP/2 协议层流错误（Curl error 92: INTERNAL_ERROR），导致多个 RPM 包（git-core、gcc-c++、guile）下载中断；`guile`（git 的传递依赖）在耗尽所有镜像重试后仍下载失败，`dnf install` 以退出码 1 终止。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个标准的 vvenc Dockerfile（基于 openEuler 24.03-lts-sp4 基础镜像，安装 git/gcc/gcc-c++/make/cmake，编译 vvenc 1.14.0），以及配套的 README、image-info.yml、meta.yml 元数据更新。Dockerfile 语法和构建逻辑均无问题，失败完全是 `repo.openeuler.org` RPM 仓库在构建时段的 HTTP/2 网络不稳定所致。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码，重试即可。** 这是 CI 基础设施层面的临时网络问题（RPM 仓库服务端 HTTP/2 连接异常），与 PR 代码变更完全无关。Code Fixer 无需处理。建议在 Jenkins 上手动重新触发该 job 的构建重试（rerun/replay），待 repo.openeuler.org 的网络状态恢复后构建即可通过。

### 方向 2（置信度: 低）
若多次重试仍持续失败，可考虑在 Dockerfile 的 `dnf install` 命令前添加 `dnf makecache` 并设置 `ip_resolve=4`（禁用 IPv6）或降低 HTTP 协议版本（如强制 HTTP/1.1），以规避 HTTP/2 层的协议错误。但这属于对基础设施问题的 workaround，不应作为首选方案。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段（2026-07-09 14:09 UTC）是否存在已知的服务端 HTTP/2 层问题或负载异常
- 确认同一时段其他使用 `dnf install` 的 aarch64 构建 job 是否也出现相同类型的 Curl error (92)
- 确认 x86_64 架构的构建 job 日志是否也出现同样的 HTTP/2 stream error（本次日志仅包含 aarch64 构建）

## 修复验证要求
无需验证（infra-error，非代码修复范畴）。若采用方向 2（workaround），需在 aarch64 runner 上重新触发构建并确认所有 RPM 包均下载成功。
