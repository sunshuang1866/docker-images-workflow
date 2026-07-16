# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
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
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install` 步骤）
- 失败原因: CI 构建节点 `ecs-build-docker-aarch64-04-sp` 在通过 `repo.openeuler.org` 下载 aarch64 RPM 包时，镜像站 HTTP/2 连接频繁出现流层错误（INTERNAL_ERROR），yum 重试机制使得前 3 个出错包（gcc、kernel-headers、perl-MIME-Base64）最终下载成功，但 `vim-common`（第 173/173 个包，7.8MB）在耗尽所有镜像后彻底失败，导致整个 `yum install` 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 在语法和依赖声明上没有错误——`yum install` 的包列表完整且正确（gcc、gcc-c++、cmake、openssl-devel、gflags-devel、protobuf-devel、leveldb-devel、snappy-devel 等均被正确声明）。失败纯粹由 `repo.openeuler.org` 在 aarch64 架构上的 HTTP/2 服务不稳定引起，属于 CI 基础设施层的传输问题。日志中可见在下载周期（#7 持续约 21 分钟）内共出现 4 次不同包的传输层错误，说明镜像站在此期间存在系统性的 HTTP/2 连接异常。

## 修复方向

### 方向 1（置信度: 高）
**手动重试 CI 构建**。该失败为临时性网络波动，`repo.openeuler.org` 镜像站的 HTTP/2 服务不稳定是瞬时问题。在镜像站恢复后重新触发 CI job，有很大概率直接通过。无需对 Dockerfile 做任何修改。

### 方向 2（置信度: 中）
若重试多次仍然失败且均表现为同一镜像站 HTTP/2 错误，可在 Dockerfile 的 `yum install` 命令中增加下载重试次数（`yum install --setopt=retries=10`），或考虑换用其他 openEuler 镜像源（如华为云镜像 `repo.huaweicloud.com/openeuler`），提高网络容错能力。但此为降级方案，首推方向 1。

## 需要进一步确认的点
- `repo.openeuler.org` 在 CI 构建时段（2026-07-09 13:45 UTC 左右）是否存在已知的 HTTP/2 服务降级或维护事件。
- 同一时段其他 aarch64 PR 的 CI job 是否也出现了相同的 Curl error (92) 模式——若有多起，说明是镜像站系统性故障而非偶发。
- 若重试后仍然失败，需确认 `ecs-build-docker-aarch64-04-sp` 节点到 `repo.openeuler.org` 的网络连通性和 HTTP/2 协商是否正常。

## 修复验证要求
无需修复验证。本次失败为 infra-error，Code Fixer 无需处理。建议由 CI 管理员手动重试 Job 即可。
