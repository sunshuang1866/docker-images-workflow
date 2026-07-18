# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库网络抖动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, repo.openeuler.org, No more mirrors to try

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
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: openEuler 官方软件仓库（`repo.openeuler.org`）在 aarch64 runner 构建期间出现间歇性 HTTP/2 网络故障，导致多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64）下载失败后自动重试成功，但最后一个包 `vim-common` 在耗尽所有镜像尝试后仍下载失败，yum 退出码 1。

### 与 PR 变更的关联
**无关**。本次失败是 CI 基础设施层面的网络问题（`repo.openeuler.org` 仓库端 HTTP/2 连接不稳定），与 PR 新增的 Dockerfile 内容完全无关。Dockerfile 中 `yum install` 指定的所有包名在仓库中均存在且正确（前 172 个包已成功下载），仅因仓库网络抖动导致最后一个包永久失败。PR 代码变更无任何错误。

## 修复方向

### 方向 1（置信度: 高）
**直接重试 CI 构建**。本次失败为 `repo.openeuler.org` 的临时性网络故障，PR 的 Dockerfile 和元数据文件均无问题。重新触发 CI 构建大概率会成功（网络恢复后 173 个 RPM 包均可正常下载）。

### 方向 2（可选，置信度: 低）
若重试多次仍失败，可考虑在 Dockerfile 的 `yum install` 命令中增加重试参数（如 `yum --setopt=retries=10 --setopt=timeout=60 install -y ...`），以提高对偶发网络波动的耐受能力。但此方向为防御性优化而非必要的修复。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 当前服务状态（是否正在经历维护或降级）
- 若持续失败，需确认 aarch64 runner `ecs-build-docker-aarch64-04-sp` 的网络连通性
