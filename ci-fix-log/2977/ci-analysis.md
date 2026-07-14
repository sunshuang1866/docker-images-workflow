# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: yum仓库网络抖动
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 framing layer, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, Error downloading packages, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 runner 上执行 `yum install` 从 `repo.openeuler.org` 下载 RPM 包时，仓库服务器多次出现 HTTP/2 流层错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接中断（Curl error 56: SSL_ERROR_SYSCALL），导致多个包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载失败。经过 yum 自动重试后，`vim-common` 包最终因所有镜像源均已尝试仍无法下载而永久失败，整个 `yum install` 步骤返回 exit code 1。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 新增的 Dockerfile 内容（`yum install` 包列表和 cmake 构建参数）语法正确、无逻辑错误。失败完全由 openEuler 24.03-LTS-SP4 软件仓库 `repo.openeuler.org` 在构建期间发生的网络层 / HTTP/2 服务端不稳定导致，属于 CI 基础设施问题。同一个 `yum install` 步骤中已有 170+ 个包成功下载并安装（日志显示 172/173 包下载完成），仅最后 1 个包 `vim-common` 因持续的网络错误而失败。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。此失败为 `repo.openeuler.org` 仓库服务器的临时性网络波动所致，与 Dockerfile 代码无关。在仓库服务恢复稳定后重新触发 CI 构建（如 `/retest` 或重新 push）即可通过。无需修改任何代码。

### 方向 2（置信度: 低）
如果该镜像仓库的 HTTP/2 连接问题持续出现，可考虑在 Dockerfile 的 `yum install` 前添加 `yum` 重试配置（如 `echo 'retries=10' >> /etc/yum.conf`），或在 `yum install` 命令本身增加重试逻辑。但这只是缓解措施，根本问题仍需上游仓库运维方处理 HTTP/2 服务端稳定性。

## 需要进一步确认的点
- `repo.openeuler.org` 在构建时间（2026-07-09 13:45 UTC ~ 14:10 UTC 左右）是否存在已知的 CDN/HTTP/2 服务中断或降级事件。
- aarch64 仓库的 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 文件大小约 7.8 MB，大文件下载更容易受 HTTP/2 流中断影响，是否存在持续性问题。
- 同一时间段的 x86_64 runner 构建（如果也有 brpc 或其他镜像的 SP4 Dockerfile 构建）是否遇到同类 `repo.openeuler.org` 下载失败，以确认是仓库全局问题还是单个 aarch64 runner 的网络问题。
