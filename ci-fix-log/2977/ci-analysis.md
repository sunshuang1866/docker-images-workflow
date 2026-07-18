# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Yum仓库网络波动
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum install

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: `repo.openeuler.org` 在 aarch64 架构构建节点的 yum 包下载过程中出现间歇性网络故障（HTTP/2 流被异常关闭、SSL 连接重置），导致多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载失败，最终 vim-common 因所有镜像源尝试完毕仍无法下载而失败，整个 `yum install` 步骤退出码为 1。

### 与 PR 变更的关联
**无关**。本次 PR 仅新增了一个 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）并更新了 README.md、image-info.yml 和 meta.yml 中的条目。Dockerfile 中 `yum install` 列出的依赖包（git、gcc、gcc-c++、make、cmake、openssl-devel、gflags-devel、protobuf-devel、protobuf-compiler、abseil-cpp-devel、leveldb-devel、snappy-devel）均为 openEuler 24.03-LTS-SP4 仓库中的合法包名，失败原因是构建时仓库网络不稳定，与 PR 代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**重试即可**。这是 `repo.openeuler.org` 临时网络波动导致的构建失败，无需修改 Dockerfile 或任何代码。在 CI 中重新触发构建，等待仓库恢复网络连通性后应能通过。

## 需要进一步确认的点
- 检查 `repo.openeuler.org` 在 aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）上的网络连通性和稳定性。如果该问题频繁发生，可能需要：
  1. 为 aarch64 构建节点配置更稳定的镜像源或本地缓存代理
  2. 在 Dockerfile 的 `yum install` 前添加 `yum makecache` 并配置重试参数（如 `retries=10, timeout=60`）
- 确认 jenkins job 是否有自动重试机制，如果没有，建议在 trigger job 层面添加对这类网络波动错误的自动重试。
