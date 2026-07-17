# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库下载网络故障
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
#7 ERROR: process "/bin/sh -c yum install -y ... " did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方软件仓库（`repo.openeuler.org`）在 aarch64 runner 上出现间歇性网络故障，HTTP/2 流传输多次中断（Curl error 92、Curl error 56），导致 gcc、kernel-headers、perl-MIME-Base64 等 RPM 包下载失败后切换镜像重试，最终 vim-common 包耗尽所有镜像仍无法下载成功，yum install 退出码为 1。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了一个标准的 brpc Dockerfile（安装依赖 → git clone 源码 → cmake 构建），Dockerfile 内容本身无明显错误。失败发生在 `yum install` 从远端仓库下载 RPM 包的阶段，属于 CI 构建环境与 openEuler 镜像站之间的网络连接问题，不是 PR 代码变更导致。

## 修复方向

### 方向 1（置信度: 高）
**无需对 PR 代码做任何修改。** 此失败为瞬态网络基础设施故障，应在 CI 层面重试构建（re-run the failed job）。如果此类问题频繁出现，可在 CI pipeline 或 Dockerfile 层面为 `yum install` 添加重试机制（如 `yum install -y ... || yum install -y ...`）。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 aarch64 构建节点的网络连通性是否稳定（是否为特定时段或特定节点的间歇性问题）。
- 如果同类问题在多个 PR 中反复出现，需排查是否需要为 aarch64 runner 配置更近的镜像站或代理缓存。

## 修复验证要求
无。此失败与 PR 代码变更无关，无需修改 Dockerfile 或任何源文件。
