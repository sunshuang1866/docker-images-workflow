# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, SSL_ERROR_SYSCALL, repo.openeuler.org, No more mirrors to try

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]

#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install` 步骤）
- 失败原因: CI aarch64 构建节点在 `yum install` 阶段从 `repo.openeuler.org` 下载 RPM 包时，遭遇 openEuler 官方仓库的 HTTP/2 流传输错误（Curl error 92: INTERNAL_ERROR）及 SSL 读取失败（Curl error 56: SSL_ERROR_SYSCALL），导致多个包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载失败，最终因 vim-common 包无可用镜像而构建中断。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个遵循现有 SP3 同构模式的 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）、更新了 README.md 表格和 image-info.yml 元数据，以及 meta.yml 的版本映射。失败发生在 Docker 构建的基础阶段——从 `repo.openeuler.org` 下载系统 RPM 包时因仓库源网络不稳定而中断，Dockerfile 中的 `yum install` 命令和包列表本身没有错误。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。该失败是 openEuler 官方 RPM 仓库 `repo.openeuler.org` 在构建时段出现 HTTP/2 传输异常导致的 transient infra 故障。建议：
- 在 CI 流水线中重新触发该 job（rerun），等待仓库源恢复后重试构建。
- 若多次重试仍失败，可考虑在 Dockerfile 的 `yum install` 前增加 `yum-config-manager` 设置重试次数或更换镜像源，但这并非 PR 变更范围的问题。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段的服务状态（是否存在 CDN 节点故障或 HTTP/2 配置变更）。
- 确认 aarch64 runner 节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路稳定性。
- 若该问题持续复现，需考虑在 CI 环境中为 yum 配置重试策略或备用镜像源。
