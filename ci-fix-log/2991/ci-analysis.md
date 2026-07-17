# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: HTTP/2流错误导致RPM下载失败
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR (err 2), dnf install, repo.openeuler.org, No more mirrors to try

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: CI 的 aarch64 runner 从 `repo.openeuler.org` 下载 RPM 包时，多个包（`git-core`、`gcc-c++`、`guile`）持续遭遇 HTTP/2 流错误（Curl error 92: `INTERNAL_ERROR (err 2)`）。其中 `git-core` 和 `gcc-c++` 在重试后成功下载，但 `guile` 的传输始终失败，耗尽所有镜像后 `dnf install` 退出码 1。这是 `repo.openeuler.org` 服务器端 HTTP/2 实现的间歇性问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了一个标准格式的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中使用的 `dnf install -y git gcc gcc-c++ make cmake` 是合法的包名和语法，所有包在 openEuler 24.03-LTS-SP4 仓库中均存在（日志显示依赖解析成功，列出 156 个待安装包）。失败发生在 `repo.openeuler.org` 的 HTTP/2 传输层，属于 CI 基础设施/网络层面的问题。

## 修复方向

### 方向 1（置信度: 高）
**问题是 repo.openeuler.org 的 HTTP/2 服务器对 aarch64 runner 的间歇性流错误，不属于代码缺陷。** 无需修改 Dockerfile 或任何 PR 文件。等待 `repo.openeuler.org` 服务端 HTTP/2 问题恢复后，重试 CI 构建（re-trigger the failed job）即可。

### 方向 2（置信度: 中）
如果 `repo.openeuler.org` 的 HTTP/2 问题持续存在，可考虑在 Dockerfile 中 `dnf install` 之前，通过添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置 `echo "retries=10"` 来规避 HTTP/2 传输问题，但这只是临时绕行方案，不建议作为正式修复。

## 需要进一步确认的点
- `repo.openeuler.org` 的 HTTP/2 服务当前状态：该服务器是否对 aarch64 架构的特定包（如 `guile`、`gcc-c++`）存在已知的传输问题？建议联系 openEuler 基础设施团队确认。
- 如果相同 runner（`ecs-build-docker-aarch64-04-sp`）在其他 PR 上也出现同类 Curl error (92)，则确认为服务端基础设施问题；如果仅此 PR 出现，需要确认 runner 本地网络环境。

## 修复验证要求
不适用（infra-error，无需代码修复）。如需验证，直接 re-trigger CI 构建，确认 `repo.openeuler.org` HTTP/2 问题已恢复后构建可正常通过。
