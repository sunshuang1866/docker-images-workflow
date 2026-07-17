# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库下载网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4` — `RUN yum install -y ...` 步骤
- 失败原因: aarch64 构建节点在从 `repo.openeuler.org` 下载 RPM 包时遭遇多次 HTTP/2 传输层错误（Curl error 92: HTTP/2 stream INTERNAL_ERROR）和 SSL 读取失败（Curl error 56: SSL_ERROR_SYSCALL），多个包（gcc、kernel-headers、perl-MIME-Base64）出现间歇性下载错误，其中 vim-common 最终耗尽所有镜像重试机会，导致整个 yum install 步骤失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的是一个标准的 Dockerfile，`yum install` 步骤中列出的所有包均为 openEuler 24.03-LTS-SP4 官方仓库中存在的标准系统包，Dockerfile 本身没有语法或配置错误。失败的原因是构建时 `repo.openeuler.org` 仓库服务端 HTTP/2 连接不稳定，属于 CI 基础设施网络问题。日志中早期包（如 acl、abseil-cpp、binutils 等）下载成功，但后续大批量并发下载时频繁出现 HTTP/2 stream 错误，表明这是仓库服务端在高负载或特定时段的不稳定表现。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。这是典型的网络波动导致的瞬时失败，`repo.openeuler.org` 在少量并发下载时表现正常（前 30 个包均下载成功），但在后续高并发下载阶段出现 HTTP/2 传输层错误。等待仓库服务恢复后重新触发 CI 构建即可通过。

### 方向 2（置信度: 低）
**在 Dockerfile 中添加 yum 重试机制**。在 `yum install` 命令中添加 `--setopt=retries=10` 或使用 `yum makecache && yum install -y ...` 预处理元数据，增加网络波动的容忍度。但考虑到同一构建中其他包均下载成功而仅 vim-common 彻底失败，说明重试机制可能已被 yum 默认启用且已耗尽，添加额外重试未必能根本解决。

## 需要进一步确认的点
1. `repo.openeuler.org` 在构建时间点（2026-07-09 13:44 UTC）的 aarch64 仓库 HTTP/2 服务是否存在已知中断或降级。
2. 当前 PR 在其他架构（amd64）节点上的构建结果是否通过，日志中仅提供了 aarch64 构建失败的记录。
3. 同一时段其他 PR 的 aarch64 构建是否也出现类似 Curl error 92/56，以确认是否为仓库全局性问题。

## 修复验证要求
无。本次失败为 infra-error，无需对 PR 代码做任何修改。
