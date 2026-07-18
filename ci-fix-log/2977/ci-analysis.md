# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 stream, No more mirrors to try, INTERNAL_ERROR, SSL_ERROR_SYSCALL

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI aarch64 runner 从 `repo.openeuler.org` 下载 173 个 RPM 包时，多个包遭遇到 HTTP/2 帧层错误（Curl error 92）和 SSL 读取错误（Curl error 56），其中 gcc、kernel-headers、perl-MIME-Base64 在重试后成功下载，但 vim-common 最终耗尽所有镜像重试次数后下载失败，导致 yum install 以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个标准的 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`），其中 `yum install` 命令列出的软件包（git、gcc、gcc-c++、make、cmake、which、openssl-devel、gflags-devel、protobuf-devel、protobuf-compiler、abseil-cpp-devel、leveldb-devel、snappy-devel）均为 openEuler 24.03-LTS-SP4 仓库中的标准包，Dockerfile 语法和包名均正确无误。失败完全由 `repo.openeuler.org` 镜像站在构建期间（2026-07-09 13:44~14:09 UTC）的网络波动导致，属于临时性 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 该失败为 `repo.openeuler.org` 镜像站 aarch64 仓库的临时网络故障（HTTP/2 流异常中断、SSL 连接重启），与本次 PR 的 Dockerfile 内容无关。建议直接触发 CI 重新构建（retry），镜像站网络恢复后构建应能通过。

## 需要进一步确认的点

- 确认 `repo.openeuler.org` 镜像站在 `2026-07-09 13:44~14:09 UTC` 时间段是否存在已知的 aarch64 仓库服务中断或网络抖动。
- 如果多次重试均在同一软件包（如 vim-common）失败，可考虑是否为该特定 RPM 的 CDN 缓存问题，联系 openEuler 基础设施团队检查 CDN 节点状态。
