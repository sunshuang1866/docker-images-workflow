# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: yum 仓库网络连接异常
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 stream, No more mirrors to try, repo.openeuler.org, vim-common

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
- 失败位置: `Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: CI 在 aarch64 runner 上构建时，从 `repo.openeuler.org` 下载 `vim-common` 包过程中遭遇多次 HTTP/2 连接异常（Curl error 92: INTERNAL_ERROR）和 SSL 读取失败（Curl error 56: SSL_ERROR_SYSCALL），yum 重试所有镜像后仍无法完成下载，导致构建失败。

### 与 PR 变更的关联
**与 PR 改动的代码无关。** 这是 openEuler 官方软件仓库（`repo.openeuler.org`）在 aarch64 架构节点上的网络传输不稳定导致的基础设施问题。日志显示多个 RPM 包都遭遇了间歇性 HTTP/2 流错误（gcc、kernel-headers、perl-MIME-Base64），其中大部分在重试后成功下载，只有 `vim-common` 因所有镜像均重试失败而最终报错。PR 仅新增了合法的 Dockerfile，其 `yum install` 命令语法正确、依赖包名有效。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改，等待重试。** 这是 `repo.openeuler.org` 仓库在构建期间的临时网络波动或服务端 HTTP/2 连接管理问题。yum 镜像重试机制已经正确工作（前 172 个包中多数成功下载），但 `vim-common` 很不幸是最后一个包且重试全部失败。建议：
- 重新触发 CI 构建，网络波动很可能在下次构建时自行恢复
- 若连续多次重试均在同一包失败，则需联系 openEuler 镜像站运维确认 `repo.openeuler.org` 的 aarch64 包分发是否正常

### 方向 2（置信度: 低）
**在 Dockerfile 中增加 yum 重试参数。** 如果该仓库的网络波动是常态而非偶发，可以在 `yum install` 命令前设置更激进的重试和超时策略，例如 `yum install --setopt=retries=10 --setopt=timeout=30 -y ...`。不过这是防御性措施，不应作为首选修复方案。

## 需要进一步确认的点
- 是否同一天其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 CI 构建也遭遇了类似的网络错误（检查相邻构建的历史记录，确认是系统性基础设施故障还是孤立事件）
- `repo.openeuler.org` 在构建时间段（UTC 13:44~14:07，2026-07-09）是否存在已知的网络或服务状态问题
- 构建机器 `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络路由是否正常（HTTP/2 INTERNAL_ERROR 可能由中间代理设备导致）
