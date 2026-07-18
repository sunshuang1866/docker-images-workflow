# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Yum仓库HTTP/2网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), Stream error in the HTTP/2 framing layer, SSL_ERROR_SYSCALL, No more mirrors to try, yum install, aarch64, repo.openeuler.org

## 根因分析

### 直接错误

```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
```

### 根因定位

- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在通过 `yum` 从 `repo.openeuler.org` 下载 RPM 包时，遭遇多次 HTTP/2 协议层错误（Curl error 92: Stream error）和 SSL 传输中断（Curl error 56: SSL_ERROR_SYSCALL），其中 `gcc`、`kernel-headers`、`perl-MIME-Base64` 在重试后成功，但 `vim-common`（7.8 MB）重试耗尽所有镜像后仍失败，导致整个 `yum install` 命令退出码为 1。

### 与 PR 变更的关联

**与 PR 变更无关。** PR 仅新增了一个标准的 brpc 1.16.0 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）及相关元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `yum install` 命令语法正确，所列包名均合法有效（从日志可见 yum 已正确解析依赖并开始下载173个包）。失败完全由 openEuler 24.03-LTS-SP4 aarch64 软件仓库 `repo.openeuler.org` 的网络不稳定导致，属于 CI 基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。日志中多个包（gcc、kernel-headers、perl-MIME-Base64）均在 Curl 失败后通过自动重试成功下载，仅 `vim-common` 的重试次数耗尽。这表明 `repo.openeuler.org` 的 aarch64 仓库存在间歇性网络波动，而非仓库内容缺失或包版本错误。直接重新触发 CI 构建（retrigger / re-run）有很大概率成功。

### 方向 2（置信度: 中）
**在 Dockerfile 的 yum 命令中添加重试参数**（如 `yum install --setopt=retries=10 ...`），增加重试次数以提高对网络波动的容忍度。但注意这仅是一种防御性措施——本次的根因是 `repo.openeuler.org` 仓库不稳定，重试多次后仍有一个包（vim-common）的镜像全部耗尽，增加重试次数未必能解决问题。

## 需要进一步确认的点

1. **仓库可用性**：openEuler 24.03-LTS-SP4 aarch64 仓库 `repo.openeuler.org` 的 HTTP/2 服务是否持续不稳定？建议在 CI 环境外单独测试 `curl -v` 下载失败包 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 以确认是仓库端问题还是 CI 网络链路问题。
2. **同架构其他镜像**：此 PR 仅新增了 brpc 镜像，若 aarch64 runner 上其他 openEuler 24.03-LTS-SP4 镜像构建也出现类似 `yum install` 网络错误，则进一步确认是 `repo.openeuler.org` 的普遍性问题而非本 PR 特例。
3. **重试结果**：若 re-run CI 后仍持续失败，需排查 CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）的出网链路是否对 `repo.openeuler.org`（HTTPS over HTTP/2）存在特别的流量限制或中间网络设备干扰。

## 修复验证要求

无需验证。此失败为 infra-error（网络问题），与 PR 代码变更无关，code-fixer 无需进行任何代码级修复。建议直接重新触发 CI 构建。
