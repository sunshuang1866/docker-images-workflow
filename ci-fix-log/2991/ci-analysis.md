# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源 HTTP/2 流错误
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR, dnf, repo.openeuler.org, guile, No more mirrors to try

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`dnf install` 步骤）
- 失败原因: CI 构建节点（`ecs-build-docker-aarch64-04-sp`，aarch64）在通过 `dnf` 从 `repo.openeuler.org` 下载 RPM 包时，多个包（`git-core`、`gcc-c++`、`guile`）遭遇 HTTP/2 协议层流错误（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`）。`guile` 包在重试所有镜像后仍下载失败，导致 `dnf install` 以 exit code 1 结束。这是 openEuler 软件源服务器端或网络层的瞬时故障，与 PR 的代码变更无关。

### 与 PR 变更的关联
PR 变更仅添加了 vvenc 1.14.0 在 openEuler 24.03-LTS-SP4 上的新 Dockerfile 及配套的 README、image-info.yml、meta.yml 元数据文件。Dockerfile 中的 `dnf install -y git gcc gcc-c++ make cmake` 命令语法正确，包名有效，软件源 URL 由基础镜像内置的 repo 配置决定。构建失败完全由软件源服务器端的 HTTP/2 协议故障导致，**与 PR 变更无关**。该失败在 CI 基础设施恢复后重新触发即可通过。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。此失败为 CI 基础设施/网络瞬时故障（`repo.openeuler.org` 软件源 HTTP/2 流层错误），属于 infra-error 类型。Code Fixer 不需要对 Dockerfile 或任何代码文件做修改。建议在 CI 中重新触发构建（re-trigger），网络恢复后构建应能正常通过。

## 需要进一步确认的点
- `repo.openeuler.org` 的 aarch64 软件源在构建时段是否存在已知的 HTTP/2 协议稳定性问题
- 该 CI runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否稳定，是否需要配置 dnf 的 HTTP/1.1 降级回退策略或增加重试次数
- 如果同一 job 反复出现该问题，可考虑将 dnf 配置中的 `max_parallel_downloads` 降低以减轻 HTTP/2 多路复用压力，或禁用 HTTP/2（设置 `http2=False` in dnf.conf proxy settings），但这是 CI 平台层面的调整，不涉及 PR 代码变更
