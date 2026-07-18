# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), repo.openeuler.org, No more mirrors to try

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
- 失败位置: `Dockerfile:6` — `RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`
- 失败原因: `repo.openeuler.org` 在向 aarch64 架构 runner 提供 RPM 包下载时，多次出现 HTTP/2 流内部错误（`Curl error (92): Stream error in the HTTP/2 framing layer ... INTERNAL_ERROR (err 2)`）。受影响的包包括 `git-core`、`gcc-c++`（两次）、`guile`，其中 `guile` 的下载在所有镜像源重试后均失败，导致 `dnf install` 整体失败（exit code: 1）。这是 openEuler 官方软件仓库 `repo.openeuler.org` 的 HTTP/2 服务端问题，与 PR 代码变更完全无关。

### 与 PR 变更的关联
PR 变更内容为新增 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`（含 README.md 和 meta.yml 更新），Dockerfile 中的 `dnf install` 命令完全正确（`dnf install -y git gcc gcc-c++ make cmake`），是标准的构建依赖安装步骤。失败发生在 `repo.openeuler.org` 软件源服务端，属于 CI 基础设施 / 外部依赖问题，与 PR 代码无关。该 Dockerfile 本身无需修改。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。这是 `repo.openeuler.org` 软件源的临时 HTTP/2 服务端问题（INTERNAL_ERROR），属于间歇性网络/基础设施故障。等待 openEuler 软件源服务恢复后重新触发 CI 构建即可。Code Fixer 无需对 Dockerfile 做任何修改。

## 需要进一步确认的点
- `repo.openeuler.org` 的 HTTP/2 服务端状态：该错误是间歇性还是持续性的？建议在确认软件源恢复后重新触发 CI。
- 构建 runner 节点 `ecs-build-docker-aarch64-04-sp` 与 `repo.openeuler.org` 之间的网络是否稳定：日志中前几个包（acl、cmake-data 等小包）下载成功，大包（gcc 30MB、git-core 11MB 等）下载过程中频繁出现 HTTP/2 stream 错误，提示服务端在处理长时间连接时存在问题。
