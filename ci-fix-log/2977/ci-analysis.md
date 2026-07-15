# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络不稳定
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install, aarch64

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
- 失败位置: `Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: CI 构建节点（`ecs-build-docker-aarch64-04-sp`）到 openEuler 官方软件仓库 `repo.openeuler.org` 的网络连接不稳定，多个 aarch64 RPM 包下载过程出现 HTTP/2 流错误（`INTERNAL_ERROR`）和 SSL 读取错误（`SSL_ERROR_SYSCALL`），其中 `vim-common` 包在所有镜像源重试均失败后导致构建终止。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了一个 Dockerfile 及配套的元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中的 `yum install` 命令语法和包名均正确。失败完全由 CI 运行时与上游软件仓库之间的网络不稳定导致，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
此失败为 **infra-error**，无需修改 PR 代码。处理方式：
- 在 CI 中重新触发构建（retry），网络问题通常为暂时性波动，重试后大概率可通过。
- 如果持续失败，排查 CI 构建节点 `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络链路质量，或考虑在该节点配置本地 RPM 缓存/代理。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI 构建时段是否存在服务端异常或 CDN 节点故障。
- 确认同一 PR 的 x86_64 架构构建是否也出现类似网络问题（当前日志仅覆盖 aarch64 架构）。
- 如果重试后仍持续失败，需检查 CI 节点网络配置（DNS、代理、防火墙）是否有变更。
