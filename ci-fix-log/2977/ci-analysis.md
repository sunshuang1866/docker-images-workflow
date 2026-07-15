# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, All mirrors were already tried without success, aarch64

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库持续出现 HTTP/2 帧错误（Curl error 92: INTERNAL_ERROR）和 SSL 读错误（Curl error 56），导致 4 个 RPM 包下载失败。其中 gcc、kernel-headers、perl-MIME-Base64 在重试后成功，而 vim-common（7.8 MB）最终耗尽所有镜像重试，yum 安装失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个标准的 Dockerfile（从 `openeuler/openeuler:24.03-lts-sp4` 基础镜像出发，用 `yum install` 安装 brpc 构建依赖），以及 README.md、image-info.yml、meta.yml 的配套文档更新。Dockerfile 中 `yum install` 的包列表（git、gcc、gcc-c++、cmake、openssl-devel、gflags-devel、protobuf-devel、protobuf-compiler、abseil-cpp-devel、leveldb-devel、snappy-devel）均为常规包，无拼写错误或版本指定错误。

失败原因是 CI aarch64 构建环境与 `repo.openeuler.org` 之间的网络连接不稳定（HTTP/2 流错误），属于基础设施问题。日志中同一个构建任务内，多个无关包（gcc、kernel-headers、perl-MIME-Base64、vim-common）先后出现同类网络错误，进一步确认了网络层面的问题而非包本身缺失。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 运行。** 这是典型的临时性网络波动问题（`repo.openeuler.org` 的 HTTP/2 服务端在部分请求中返回 INTERNAL_ERROR），与 PR 代码变更完全无关。等待上游仓库网络恢复后重跑 CI 即可通过。

## 需要进一步确认的点
- 如果多次重跑 CI 仍然在同一个包（vim-common）上失败，可能需要确认 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 在 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/` 中是否确实存在且完整。
- 如果同类 HTTP/2 错误频繁发生在 aarch64 runner 上，建议 CI 运维团队检查 `repo.openeuler.org` 的服务端 HTTP/2 配置或 aarch64 runner 的网络代理/MTU 设置。
