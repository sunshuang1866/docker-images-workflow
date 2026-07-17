# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: DNF仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, dnf install

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
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 步骤）
- 失败原因: CI 构建节点（`ecs-build-docker-aarch64-04-sp`，aarch64 架构）通过 HTTP/2 从 `repo.openeuler.org` 下载 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 时，`repo.openeuler.org` 服务器端 HTTP/2 流异常关闭（`INTERNAL_ERROR (err 2)`），DNF 自动重试所有镜像均失败后退出（exit code: 1）。日志中同时记录了 `git-core` 和 `gcc-c++` 包也遭遇了同类 HTTP/2 流错误，但因 DNF 重试机制最终下载成功。

### 与 PR 变更的关联
**与 PR 变更无关**。该 PR 的变更仅包含：
1. 新增 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`（新的 Docker 镜像构建文件）
2. 更新 `Others/vvenc/README.md` 和 `Others/vvenc/doc/image-info.yml`（添加新镜像版本的文档条目）
3. 更新 `Others/vvenc/meta.yml`（注册新的 image tag）
Dockerfile 中的 `dnf install` 命令语法正确，不存在拼写错误或参数问题。失败完全由 `repo.openeuler.org` 仓库服务器端 HTTP/2 协议层面的网络传输故障导致，属于 CI 基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码**。这是一个 CI 基础设施/网络问题（`infra-error`），Dockerfile 和 PR 变更本身没有错误。操作建议：
- **重试 CI 构建**：待 `repo.openeuler.org` 服务器 HTTP/2 协议问题恢复后重新触发 CI，大概率可以成功通过。
- **如反复出现**：考虑在 Dockerfile 的 `dnf install` 命令前添加一次 `dnf makecache` 或在 `dnf install` 中添加 `--retries` 参数（需确认 DNF 版本支持），但通常情况下重试即可解决。

## 需要进一步确认的点
- 检查 `repo.openeuler.org` aarch64 OS 仓库的当前可用性（是否页面可访问、是否持续存在 HTTP/2 流错误）。
- 如果多次重试均在同一包（`guile`）上失败，确认 `guile-2.2.7-6.oe2403sp4.aarch64.rpm` 在仓库中是否真实存在且完整（非镜像同步损坏）。
- 确认 CI aarch64 runner (`ecs-build-docker-aarch64-04-sp`) 与 `repo.openeuler.org` 之间的网络连接质量是否正常。
