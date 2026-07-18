# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库 HTTP/2 不稳定
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, aarch64

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（yum install 步骤）
- 失败原因: aarch64 构建节点上 yum 从 `repo.openeuler.org` 下载 173 个 RPM 包时，多个包遭遇 HTTP/2 帧层错误（Curl error 92/56）。前 3 个包（gcc、kernel-headers、perl-MIME-Base64）通过重试成功下载，但第 173 个包（vim-common）在耗尽所有镜像重试后仍下载失败，导致整个 yum install 步骤以 exit code 1 终止。该错误与 PR 代码变更无关，属于 CI 基础设施网络问题。

### 与 PR 变更的关联
**无关。** PR 新增的 Dockerfile 语法和内容均正确——`yum install` 安装的软件包列表（git、gcc、gcc-c++、make、cmake、openssl-devel、gflags-devel、protobuf-devel、protobuf-compiler、abseil-cpp-devel、leveldb-devel、snappy-devel）均为 brpc 编译所需的合理依赖，且这些包在 openEuler 24.03-LTS-SP4 仓库中确实存在。失败原因是 `repo.openeuler.org` 在 aarch64 架构构建期间出现间歇性 HTTP/2 传输层错误，与 Dockerfile 内容无关。`vim-common` 也并非 PR 显式指定的依赖，而是 git 等包的传递依赖。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，重试 CI 即可。** 该失败为 openEuler 官方仓库（`repo.openeuler.org`）在构建期间的瞬时网络抖动（HTTP/2 帧错误 + SSL 读取错误），4 个包中有 3 个通过 yum 内置重试成功下载，仅最后一个包（vim-common）运气不佳耗尽重试次数。重新触发 CI 构建大概率可通过。若反复失败，可考虑在 `yum install` 前增加 `yum makecache` 或为 `yum install` 添加 `--retries` 参数提高容错。

### 方向 2（置信度: 低）
若重试持续失败且仅发生在该特定 aarch64 runner，可能是 runner 节点与 `repo.openeuler.org` 之间的网络链路存在问题，需要运维排查节点网络或调整 runner 分配。

## 需要进一步确认的点
- 确认同一 PR 的 x86_64（amd64）构建是否成功（日志仅包含 aarch64 job）。若 x86_64 构建成功，可进一步确证该失败为 aarch64 runner 节点或 repo.openeuler.org 对 aarch64 请求的瞬时问题。
- 确认重新触发 CI 后 aarch64 构建是否通过。若通过，则无需任何代码变更。
