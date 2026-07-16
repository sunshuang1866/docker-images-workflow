# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源网络波动
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install ...` 步骤）
- 失败原因: aarch64 构建节点从 `repo.openeuler.org` 下载 RPM 包时遭遇多次 HTTP/2 流错误（curl error 92）和 SSL 连接断开（curl error 56）。yum 的重试机制使 `gcc`、`kernel-headers`、`perl-MIME-Base64` 三个包最终重试成功，但 `vim-common` 耗尽所有镜像重试后仍失败，导致整个 `yum install` 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 新增的 Dockerfile 格式正确，`yum install` 命令中列出的软件包均为 openEuler 24.03-LTS-SP4 仓库中的标准包名。失败发生在软件包下载阶段，是 `repo.openeuler.org` 软件源在构建时段出现网络波动导致的临时性基础设施问题，重试即可恢复。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码。** 这是 openEuler 官方软件源 `repo.openeuler.org` 的临时网络波动，建议触发 CI 重试（retry）即可。日志显示大部分 173 个包下载成功，仅 `vim-common` 在多次重试后最终失败，说明软件源在构建窗口期内存在间歇性 HTTP/2 连接问题。

## 需要进一步确认的点
- 检查 openEuler 软件源 `repo.openeuler.org` 在构建时段（2026-07-09 13:44 UTC 前后）是否存在已知的可用性问题。
- 如果同样的网络问题在多日重试中持续出现，需考虑在 Dockerfile 中添加 yum 镜像源 fallback（如华为云镜像站），但当前证据表明这是临时性波动，无需立即处理。
