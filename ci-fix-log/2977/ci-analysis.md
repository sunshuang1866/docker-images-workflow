# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), Stream error in the HTTP/2 framing layer, SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum install

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install -y` 步骤）
- 失败原因: CI 在 aarch64 runner 上构建时，从 `repo.openeuler.org` 下载 RPM 包过程中遭遇多次 HTTP/2 流错误（Curl error 92：INTERNAL_ERROR）和 SSL 读取错误（Curl error 56：SSL_ERROR_SYSCALL），最终 `vim-common` 包因所有镜像源均已尝试失败而无法下载，导致 yum install 步骤整体失败。

### 与 PR 变更的关联
与 PR 无关。PR 仅新增了一个标准的 Dockerfile，其 `yum install` 命令安装的均为 openEuler 24.03-LTS-SP4 官方仓库中的常规包。失败原因是 `repo.openeuler.org` 镜像站在构建期间出现网络波动（HTTP/2 传输层异常、SSL 连接中断），属于 CI 基础设施/外部依赖问题，Dockerfile 本身语法和包名均无错误（173 个包中有 170 个已成功下载，说明包名正确且仓库可访问）。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。此为 `infra-error`，是 `repo.openeuler.org` 镜像站在构建时间段内出现网络不稳定所致。建议重新触发 CI 构建（retry），在网络正常时段通常可自动通过。若持续复现，需联系 openEuler 基础设施团队排查镜像站 HTTP/2 服务端问题。

## 需要进一步确认的点
- 同一时间段内其他 PR 的 CI 构建是否也出现类似 `repo.openeuler.org` 下载失败（若有多例，可确认是镜像站侧问题而非个别构建环境问题）。
- `repo.openeuler.org` 的 HTTP/2 服务在构建时间点（2026-07-09 13:44 UTC 前后）是否存在已知故障或维护窗口。

## 修复验证要求
无。此为 infra-error，不涉及对 Dockerfile 或源码的修改。
