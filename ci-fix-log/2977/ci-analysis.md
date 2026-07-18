# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), OpenSSL SSL_read: SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum install

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
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方包仓库 `repo.openeuler.org` 在 CI 构建时段（aarch64 节点）存在 HTTP/2 连接不稳定问题，多个 RPM 包下载过程中出现 Curl error (92) (HTTP/2 stream INTERNAL_ERROR) 和 Curl error (56) (SSL_ERROR_SYSCALL)，其中 `vim-common` 包在重试耗尽所有镜像后仍下载失败，导致 `yum install` 步骤整体退出码为 1。

### 与 PR 变更的关联
与 PR 变更**无关**。该 PR 仅新增了一个 brpc 1.16.0 的 Dockerfile 及相关元数据/文档文件。Dockerfile 内容本身正确（包名、yum 命令语法均无问题），失败完全由 `repo.openeuler.org` 仓库在构建时段的网络不稳定导致。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。此失败是纯粹的 CI 基础设施问题（infra-error），由 openEuler 官方包仓库的网络/HTTP/2 服务不稳定引起。建议重新触发 CI 构建，在网络状况恢复后可自然通过。如该问题在多次重试后持续出现，需联系 openEuler 镜像站运维排查 `repo.openeuler.org` 的 HTTP/2 服务端问题。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在该时段是否存在已知的 HTTP/2 服务降级或中断。
- 如果重新触发 CI 后仍然失败，需排查是否 aarch64 构建节点到 `repo.openeuler.org` 的网络链路存在特定问题（如 HTTP/2 代理不兼容）。
