# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler镜像站HTTP/2错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, yum install, HTTP/2, SSL_ERROR_SYSCALL

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: `repo.openeuler.org` 镜像站在 aarch64 架构的构建过程中出现间歇性 HTTP/2 传输层错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致部分 RPM 包下载失败。其中 `gcc`、`kernel-headers`、`perl-MIME-Base64` 重试后成功，`vim-common` 重试后仍失败，yum 因所有镜像源均已尝试而中止安装。

### 与 PR 变更的关联
**与 PR 无关。** PR #2977 新增了一个完全标准的 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`），其 `yum install` 命令列出的所有包名均正确且存在于 openEuler 24.03-LTS-SP4 仓库中（日志中依赖解析阶段已确认全部 173 个包均可识别）。失败发生在 RPM 下载传输阶段，是远端镜像站 `repo.openeuler.org` 的网络/服务端问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建即可。** 这是一次由 `repo.openeuler.org` 镜像站 HTTP/2 服务端连接不稳定性引起的偶发 infra-error。同类失败在本次构建日志中已出现多次（gcc、kernel-headers、perl-MIME-Base64 均遇到相同错误后重试成功，仅 vim-common 在最后一轮重试中彻底失败）。在镜像站恢复稳定后重新触发 CI 构建，大概率可成功通过。

### 方向 2（置信度: 低）
若短期内反复出现同类错误，可考虑在 Dockerfile 的 `yum install` 命令中增加重试参数（如 `yum install --retries=5` 或循环重试逻辑），提高对网络波动的容忍度。但这属于 CI 基础设施侧优化而非 PR 代码缺陷。

## 需要进一步确认的点

1. 确认 `repo.openeuler.org` 在构建时段（2026-07-09 13:44 UTC）是否存在服务端 HTTP/2 协议栈异常或负载过高问题。
2. 确认 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 在镜像站是否可正常访问（可通过 wget 或 curl 直接下载验证）。
