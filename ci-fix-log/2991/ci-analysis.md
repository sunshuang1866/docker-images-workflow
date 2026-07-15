# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try, dnf install, repo.openeuler.org

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`dnf install` 从 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 仓库下载 RPM 包（特别是 `guile`、`gcc-c++`、`git-core`）时遭遇间歇性 HTTP/2 流错误（Curl error 92），其中 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 在耗尽所有镜像重试后仍下载失败，导致整个 `dnf install` 命令以 exit code 1 退出。需要安装的 156 个包中大部分（包括大型包如 gcc 30MB、cmake 13MB）下载成功，`git-core` 最终重试成功，但 `gcc-c++`（重试 2 次）和 `guile` 持续失败，表现为间歇性网络基础设施问题。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile（`Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`）语法正确，`dnf install` 命令格式与其他同类 Dockerfile 一致。失败原因是 openEuler 24.03-LTS-SP4 的 aarch64 软件仓库在通过网络下载 `guile` 等 RPM 包时发生 HTTP/2 协议层面的传输错误，属于 CI 构建环境到上游软件仓库间的网络基础设施问题。PR 本身未引入任何可能导致此类网络错误的代码变更。

## 修复方向

### 方向 1（置信度: 高）
**直接重试 CI 构建。** HTTP/2 流错误表现为间歇性（`git-core` 重试后成功，其他包多次重试失败），很可能是 `repo.openeuler.org` 在特定时段对 aarch64 架构请求的 HTTP/2 连接处理不稳定所致。重新触发 CI 构建大概率能绕过该网络波动。

### 方向 2（置信度: 低）
**若多次重试仍持续失败**，在 Dockerfile 的 `dnf install` 前增加重试/回退逻辑：
- 为 `dnf` 配置额外的备用镜像（在 `/etc/yum.repos.d/` 中添加华为云镜像等替代源）
- 或使用 `dnf install ... --setopt=retries=10` 增加 dnf 内部重试次数

## 需要进一步确认的点
1. 该 aarch64 SP4 构建节点（`ecs-build-docker-aarch64-04-sp`）是否能稳定访问 `repo.openeuler.org` 的 SP4 仓库——建议在同一节点上手动执行 `dnf install -y guile` 测试连通性。
2. 确认 openEuler 24.03-LTS-SP4 的 aarch64 仓库是否存在已知的 CDN/镜像稳定问题，以及该时段是否有其他 SP4 aarch64 构建任务也遭遇类似 HTTP/2 流错误。
3. 如果其他 SP4 PR 也遭遇相同错误，说明这是仓库侧系统性问题而非偶发网络抖动，需联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 配置。
