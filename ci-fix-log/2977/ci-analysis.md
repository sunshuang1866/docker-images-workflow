# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install -y ...` 步骤，Docker 构建 `[2/6]` 阶段）
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在通过 yum 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时，`repo.openeuler.org` 仓库镜像持续出现 HTTP/2 传输层错误（Curl error 92: `INTERNAL_ERROR`）和 SSL 读错误（Curl error 56: `SSL_ERROR_SYSCALL`）。虽然部分受影响包（gcc、kernel-headers）通过重试成功下载，但 `vim-common` 在所有镜像重试后仍失败，导致整个 `yum install` 命令以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 的改动仅为新增 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile` 及其配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `yum install` 命令语法正确、包名均为 openEuler 24.03-LTS-SP4 官方仓库的标准包（git、gcc、gcc-c++、make、cmake、which、openssl-devel、gflags-devel、protobuf-devel、protobuf-compiler、abseil-cpp-devel、leveldb-devel、snappy-devel）。失败根因是 `repo.openeuler.org` aarch64 仓库在构建时刻的网络可用性问题，而非 Dockerfile 内容错误。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，重试 CI 即可**。该失败属于 CI 基础设施临时性故障——`repo.openeuler.org` openEuler 24.03-LTS-SP4 aarch64 仓库在构建时出现 HTTP/2 传输层断续性错误。这类故障通常具有自愈性（仓库端恢复后即可通过）。建议重新触发 CI 构建。

### 方向 2（置信度: 中）
如果多次重试仍失败（说明仓库端持续不稳定），可在 Dockerfile 的 `yum install` 命令前添加重试或镜像源切换逻辑（如安装 `yum-utils` 并配置 `fastestmirror`，或设置 `ip_resolve=4` 强制 IPv4 避免 HTTP/2 层问题）。但这不是必需的代码修复，而是应对基础设施不稳定的临时加固。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在当前时间点是否恢复正常（可通过浏览器或 curl 直接访问验证）
- 确认其他 openEuler 24.03-LTS-SP4 相关的 CI job（非本次 PR）在同一时间段是否也出现类似下载失败，以判断是否为仓库端系统性故障
- 确认 CI 环境到 `repo.openeuler.org` 的网络路由是否存在间歇性问题（aarch64 runner 的网络出口可能有限制）
