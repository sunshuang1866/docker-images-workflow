# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库下载不稳定
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
#7 ERROR: process "/bin/sh -c yum install -y ... " did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: 构建过程中 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 软件仓库（aarch64 架构）出现网络不稳定，多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）在下载时遭遇 HTTP/2 流错误（Curl error 92）和 SSL 连接中断（Curl error 56），最终 vim-common 包所有镜像源均尝试失败，yum 安装整体退出码为 1。

### 与 PR 变更的关联
与 PR 变更无关。PR 新增的 Dockerfile 内容本身完全正确——`yum install` 命令语法规范、包名有效（在事务摘要中可见所有 173 个包均被正确识别并开始下载），多个包已成功下载（如 acl、abseil-cpp、cmake-data 等部分步骤成功），失败完全由上游软件仓库 `repo.openeuler.org` 临时性网络故障导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
无需修改 PR 代码。此为 `infra-error`，应重试 CI 构建（re-run the failed job）。若多次重试仍出现同类型错误，需联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 CDN/HTTP/2 层配置问题，或在 Dockerfile 的 `yum install` 前增加重试逻辑（如 `yum install -y --setopt=retries=10 ...`）以增强对仓库网络抖动的容忍度。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI 构建时段（2026-07-09 13:45 UTC）是否有服务中断或限流记录。
- 若持续复现，需排查 CI 构建节点 `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络链路是否正常。
- 如涉及多架构构建（amd64 + arm64），需补充确认 amd64 runner 上的构建是否也出现同类网络错误。
