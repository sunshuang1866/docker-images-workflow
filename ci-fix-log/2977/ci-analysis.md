# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, MIRROR, No more mirrors to try

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install -y ...` 步骤）
- 失败原因: CI aarch64 runner 从 `repo.openeuler.org` 下载 RPM 包（gcc、kernel-headers、vim-common、perl-MIME-Base64）时遭遇多次 HTTP/2 协议层传输错误（`Stream error in the HTTP/2 framing layer`、`SSL_ERROR_SYSCALL`），虽然前 3 个包均通过重试成功下载，但 `vim-common` 最终耗尽所有镜像重试后仍未成功，yum 安装整体失败。

### 与 PR 变更的关联
**与 PR 无关**。PR 新增的 Dockerfile 语法正确、依赖声明完整。失败是 aarch64 构建节点在下载 openEuler 24.03-LTS-SP4 软件源 RPM 包时遭遇网络传输层故障——该 openEuler 仓库的 HTTP/2 服务端间歇性异常关闭流连接（`INTERNAL_ERROR`），属于 CI 基础设施/上游镜像站问题。

## 修复方向

### 方向 1（置信度: 中）
重试 CI 构建。HTTP/2 流错误（`INTERNAL_ERROR`）和 SSL 读错误（`SSL_ERROR_SYSCALL`）通常为 `repo.openeuler.org` 服务端的临时性问题，多数情况下重试可恢复。日志中 gcc、kernel-headers、perl-MIME-Base64 三个包在首次 MIRROR 报错后均通过 yum 自动重试成功，仅 vim-common 的重试次数不足。

### 方向 2（置信度: 低）
若多次重试仍失败，可考虑在 Dockerfile 中为 `yum install` 添加 `--retries` 参数或增加超时时间，以增强网络波动场景下的健壮性。但需注意：这是对 CI 基础设施不稳定的一种 workaround，而非根本修复。

## 需要进一步确认的点
- `repo.openeuler.org` 的 CDN/镜像站在该时间段的可用性状态是否存在已知问题。
- 该 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）与其他 runner 的网络连通性是否存在差异。
- 同样的 Dockerfile 在 x86_64 runner 上是否能成功构建，以排除软件源本身的问题。
