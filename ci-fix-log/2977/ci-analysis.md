# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: SP4仓库HTTP/2传输中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, aarch64, yum install, No more mirrors to try

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`yum install` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `yum install` 时，从 `repo.openeuler.org` 下载 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 过程中遭遇 HTTP/2 传输层错误（Curl error 92: INTERNAL_ERROR），重试耗尽所有镜像后仍然失败。日志中另有 3 个包（gcc、kernel-headers、perl-MIME-Base64）也出现同类 MIRROR 警告但最终重试成功，说明 `repo.openeuler.org` 的 SP4 aarch64 仓库在该时段存在间歇性 HTTP/2 连接不稳定性。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据（README.md、image-info.yml、meta.yml），Dockerfile 中的 `yum install` 命令列出的包均为 openEuler SP4 仓库中的标准包，语法正确。失败根因是 CI 构建环境的 aarch64 runner 与 `repo.openeuler.org` SP4 仓库之间的网络传输问题，属于基础设施层面的瞬态故障。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI**。这是一个 transient infra-error，`repo.openeuler.org` SP4 aarch64 仓库的 HTTP/2 连接在本次构建期间不稳定。直接重新触发 CI 流水线，大概率能通过。无需修改任何代码。

### 方向 2（可选，置信度: 低）
如果多次重试均失败，可在 Dockerfile 的 `yum install` 命令前添加重试机制（如 `yum install -y ... || yum install -y ...`）或设置 `yum` 的 `retries` 参数增大容错性。但这只是缓解措施，根本问题在仓库侧。

## 需要进一步确认的点
- `repo.openeuler.org` SP4 aarch64 仓库在构建时段（2026-07-09 13:45 UTC 前后）是否存在已知的 CDN/负载均衡故障或维护事件。
- 如果重试后仍然失败，确认 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 在 `repo.openeuler.org` 上是否确实存在且可正常下载。
