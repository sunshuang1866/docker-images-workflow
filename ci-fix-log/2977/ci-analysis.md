# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, repo.openeuler.org, No more mirrors to try

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: aarch64 CI runner 在从 `repo.openeuler.org` 镜像站下载 RPM 包时，遭遇多次 HTTP/2 流错误（curl error 92: INTERNAL_ERROR）和 SSL 连接中断（curl error 56），大多数包经重试后下载成功，但 `vim-common` 包耗尽了所有镜像重试机会最终失败，导致整个 `yum install` 步骤以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个全新的 Dockerfile（brpc 1.16.0 on openEuler 24.03-LTS-SP4）及相关文档/元数据文件。Dockerfile 中的 `yum install` 命令语法和包列表完全正确，失败纯粹由 `repo.openeuler.org` 镜像站在 CI 构建时段的网络服务不稳定（HTTP/2 连接异常断开）引起。从日志可见，172/173 个包已成功下载，仅最后一个 `vim-common` 因镜像重试耗尽而失败，属于典型的一次性网络波动。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码**。这是 CI 基础设施层面的网络瞬断问题。直接触发 re-run 该 job 即可大概率通过。`repo.openeuler.org` 的 HTTP/2 流错误和 SSL 连接中断是镜像站服务侧的暂时性问题。

### 方向 2（置信度: 低）
如果重试后仍持续失败（极低概率），可在 Dockerfile 的 `yum install` 前添加重试机制（如 `yum install -y ... || yum install -y ...`），或为 yum 配置添加 `retries=10`、`timeout=60` 等参数提升容错能力。但考虑到日志中大部分包的重试都成功，只有最后一包失败，这明确指向瞬时网络问题而非系统性缺陷。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI 构建时间段（2026-07-09 13:44-13:55 UTC）是否存在已知的服务降级或网络故障。
- 如持续复现，需检查 `ecs-build-docker-aarch64-04-sp` runner 节点到 `repo.openeuler.org` 的网络链路稳定性。
