# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 framing layer, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
- 失败原因: CI aarch64 构建节点在执行 `yum install` 从 `repo.openeuler.org` 下载 RPM 包时，多次遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）和 SSL 读取失败（Curl error 56: SSL_ERROR_SYSCALL）。大部分包经 yum 自动重试后成功下载，但 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 重试耗尽所有镜像后仍未成功，导致整个 `yum install` 命令失败（exit code: 1）。

### 与 PR 变更的关联
**与 PR 无关**。该 PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（含 README.md、image-info.yml、meta.yml 的配套更新），Dockerfile 内容正确、`yum install` 命令格式规范。失败根因是 `repo.openeuler.org` 镜像站在构建时段出现网络波动，属于 CI 基础设施问题，非代码逻辑缺陷。

## 修复方向

### 方向 1（置信度: 高）
**重试构建即可**。该失败是 `repo.openeuler.org` 镜像源的临时网络波动所致（HTTP/2 流异常断开、SSL 读取失败），属于典型的 CI 基础设施瞬态故障。无需修改 Dockerfile 或任何 PR 代码，重新触发 CI 流水线有很大概率通过。

## 需要进一步确认的点
- `repo.openeuler.org` 镜像站在构建时段（2026-07-09 13:44 UTC 前后）是否存在已知服务中断或降级。
- 该 aarch64 CI runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否有持续性问题（可检查同时段其他 PR 在该节点上的构建是否也有类似 curl 错误）。
