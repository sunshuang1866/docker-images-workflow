# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler镜像仓库下载失败
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 framing layer, Stream error, No more mirrors to try, yum install, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install` 步骤）
- 失败原因: CI aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时，多次遇到 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接中断（Curl error 56: SSL_ERROR_SYSCALL），其中 `vim-common` 包（172/173 中最后一个待下载的包）在耗尽所有重试后仍未成功，导致整个 yum install 事务失败。

### 与 PR 变更的关联
与 PR 变更无关。PR 仅新增了 brpc 的 Dockerfile、README 条目、image-info 条目和 meta.yml 条目，Dockerfile 中的 `yum install` 命令语法和包名均正确（日志显示 yum 已成功解析所有 173 个依赖包并将其加入事务列表）。失败是 openEuler 官方镜像仓库在构建时间段的网络不稳定导致的，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，触发 CI 重新构建即可。** 该失败是由 `repo.openeuler.org` 镜像仓库在构建期间的网络波动（HTTP/2 流中断、SSL 连接断开）引起的暂时性基础设施问题。Dockerfile 本身语法和依赖声明均正确——yum 已成功解析全部 173 个包并下载了其中 172 个，仅最后一个包因网络耗尽重试失败。重新触发 CI 大概率可以通过。

### 方向 2（置信度: 低）
若多次重试仍失败且始终卡在 `vim-common` 包，则可能该特定版本的包（`vim-common-2:9.0.2092-36.oe2403sp4`）在镜像仓库中存在分发问题。此时需联系 openEuler 基础设施团队确认仓库同步状态。

## 需要进一步确认的点
- 若重试 CI 后仍失败，需确认 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/` 中 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 是否确实存在且可正常下载。
- 检查 CI 构建节点对 `repo.openeuler.org` 的 HTTP/2 连接是否存在持续性问题（可对比同时段其他 SP4 镜像构建是否也出现类似 curl 错误）。
