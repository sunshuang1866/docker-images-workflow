# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum download

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install` 步骤）
- 失败原因: CI 构建节点（`ecs-build-docker-aarch64-04-sp`）在 `yum install` 下载 173 个 RPM 软件包时，与 `repo.openeuler.org` 之间的 HTTP/2 连接持续出现流错误（Curl error 92: INTERNAL_ERROR）和 SSL 读取错误（Curl error 56: SSL_ERROR_SYSCALL）。部分软件包（gcc、kernel-headers、perl-MIME-Base64）经重试后下载成功，但 `vim-common` 最终耗尽所有镜像重试机会，导致 `yum install` 整体失败（exit code: 1）。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准的 brpc Dockerfile（基于 `openeuler/openeuler:24.03-lts-sp4` 基础镜像，通过 `yum install` 安装编译依赖后 cmake 构建），外加 README 和元数据文件的更新。失败发生在 `yum install` 从 openEuler 官方软件仓库下载 RPM 包的阶段，属于 CI 基础设施到 `repo.openeuler.org` 的网络连接不稳定问题。即使不引入任何 PR 变更，同一构建节点在相同时间尝试下载这些软件包也可能触发相同错误。

## 修复方向

### 方向 1（置信度: 中）
触发 CI 重新构建。此类 `repo.openeuler.org` 网络波动问题通常是临时的，重试后大概率可以通过。日志中 173 个软件包中的 169 个已成功下载（包括此前同样遭遇 Curl error 后重试成功的 gcc、kernel-headers、perl-MIME-Base64），仅 `vim-common` 在重试耗尽后最终失败，说明网络状况处于临界状态，重新触发构建时仓库可能恢复正常。

### 方向 2（置信度: 低）
若网络问题持续复现，可考虑在 Dockerfile 的 `yum install` 命令中添加 `--retries 10 --retry-delay 30` 等重试参数，提高对偶发网络波动的容忍度。但这不是根本解决方案，且需确认 CI 环境中 yum/dnf 版本支持这些参数。

## 需要进一步确认的点
- `repo.openeuler.org` 在构建时间点（2026-07-09 13:45 UTC 左右）是否存在已知的服务端 HTTP/2 或负载均衡问题。
- 该 aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络路由是否存在抖动。
- 同一时段其他 aarch64 构建任务是否也存在类似的包下载失败，以判断是节点级别还是仓库级别的网络问题。
