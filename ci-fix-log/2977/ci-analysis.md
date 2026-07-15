# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2传输中断
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, yum install, aarch64

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`repo.openeuler.org` 镜像站出现间歇性 HTTP/2 流中断和 SSL socket 错误，导致多个 RPM 包下载过程中出现 `Curl error (92)`（HTTP/2 INTERNAL_ERROR）和 `Curl error (56)`（SSL_ERROR_SYSCALL）。173 个依赖包中有 4 个遇到 curl 错误，其中 `gcc`、`kernel-headers`、`perl-MIME-Base64` 经 yum 重试后下载成功，但 `vim-common`（最后一个包，173/173）多次重试均失败，耗尽所有镜像源后 yum 报错退出。

### 与 PR 变更的关联
**与 PR 变更无关**。本次 PR 新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（及配套的 README、image-info.yml、meta.yml 更新），Dockerfile 中 `yum install` 的包列表完整且正确（gcc、gcc-c++、cmake、openssl-devel、gflags-devel、protobuf-devel 等均为 brpc 编译所需的合理依赖）。失败的直接原因是 `repo.openeuler.org` 镜像站网络服务不稳定，属于 CI 基础设施问题，并非代码错误。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复**。这是 CI 基础设施的瞬时网络故障（`repo.openeuler.org` 镜像站 HTTP/2 传输异常），与 PR 的 Dockerfile 或配置文件变更无关。建议触发 CI 重试（re-run），在网络恢复正常后应能构建成功。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 镜像站在该时间段的可用性（服务端是否发生 HTTP/2 协议层异常或 SSL 会话重置）
- 若多次重试均出现相同错误，需确认 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否存在持续性问题
