# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库网络不稳定
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, Cannot download, all mirrors were already tried without success

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y` 步骤，aarch64 架构构建）
- 失败原因: openEuler 官方软件仓库 `repo.openeuler.org` 在 aarch64 CI runner 构建期间出现网络不稳定，多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载时遭遇 HTTP/2 流错误（Curl error 92）和 SSL 连接中断（Curl error 56），最终 `vim-common` 包因所有镜像源均已尝试失败而无法下载，导致 `yum install` 整体失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、README 条目、image-info 条目和 meta.yml 条目。Dockerfile 内容正确（安装必要的构建依赖并通过 cmake 编译 brpc），没有引入任何可能导致网络问题的代码。失败完全是 `repo.openeuler.org` 镜像站在 aarch64 架构下的间歇性网络问题导致。在日志中可以看到，大部分包（172 个中的大多数）下载成功，仅少数几个包遭遇 HTTP/2 流错误，而重试后部分恢复，但 `vim-common` 最终耗尽所有镜像源后仍失败。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 该失败属于 CI 基础设施问题（openEuler 官方软件仓库网络波动），与 PR 变更无关。建议：
- 触发 CI 重试（re-run），网络恢复后构建应能通过。
- 若仓库网络不稳定问题持续，可在 Dockerfile 的 `yum install` 命令前添加重试机制（如 `yum install -y --retries=5 --retry-delay=10 ...`），但这属于防御性优化而非根因修复。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的服务状态在当前时间段是否正常（可以单独测试 aarch64 架构的包下载）。
- 确认这是否为该 CI runner 节点（`ecs-build-docker-aarch64-04-sp`）的网络问题还是仓库本身的问题——可通过在同一时间段检查其他 PR 的 aarch64 构建是否也遇到类似问题来判断。
