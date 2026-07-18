# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像下载失败
- 新模式症状关键词: Curl error, HTTP/2 framing layer, Stream error, No more mirrors to try, repo.openeuler.org, yum install

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（yum install 步骤）
- 失败原因: CI aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）在 `yum install` 阶段从 `repo.openeuler.org` 下载 RPM 包时，多个包遇到 HTTP/2 流错误（Curl error 92）和 SSL 读取错误（Curl error 56），其中 `vim-common` 包耗尽所有重试镜像后彻底失败，导致整个 yum 事务回滚。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了一个标准的 Dockerfile（安装 gcc/cmake/openssl-devel/protobuf-devel 等常规包并编译 brpc），Dockerfile 本身语法正确、依赖声明合理。失败完全由 openEuler 24.03-LTS-SP4 的 aarch64 RPM 仓库在构建时的网络不稳定导致，属于 CI 基础设施层面的瞬态故障。该 Dockerfile 在仓库网络正常时重试即可通过。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，触发 CI 重试。** 失败根因为 `repo.openeuler.org` aarch64 仓库的网络瞬态故障（HTTP/2 流中断 + SSL 连接断开），与 Dockerfile 内容无关。在 openEuler 镜像站恢复正常后，重新触发该 job 即可通过。

## 需要进一步确认的点

- `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在构建时间点（2026-07-09 13:44 UTC）是否存在 CDN 节点故障或流量过载问题。可通过对比同一时间段其他仓库（如 EPOL、everything）的下载成功率来辅助判断。
- 该构建节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路质量是否稳定。若同一节点其他 SP4 aarch64 镜像构建也频繁出现类似 Curl error，则可能是节点网络问题，需运维介入排查。
