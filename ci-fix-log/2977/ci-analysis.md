# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库网络下载失败
- 新模式症状关键词: Curl error, HTTP/2 framing layer, SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`:4-11（yum install 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `yum install` 时，从 `repo.openeuler.org` 下载多个 RPM 包时反复遭遇 Curl HTTP/2 流错误（错误码 92）和 SSL 连接中断（错误码 56），最终 `vim-common` 包（173 个待安装包中的最后一个）因所有镜像源均已尝试失败而无法完成下载，导致整个构建终止。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2977 的改动仅为：
1. 新增 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`（brpc 1.16.0 的 openEuler 24.03-LTS-SP4 构建定义）
2. 更新 `Others/brpc/README.md`、`Others/brpc/doc/image-info.yml`、`Others/brpc/meta.yml` 以注册新镜像版本

Dockerfile 中的 `yum install` 命令语法、包名及参数均正确无误，失败原因完全是 `repo.openeuler.org` 在构建时段对 aarch64 架构包的 HTTP/2 下载服务不稳定，导致多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）在传输过程中连接中断。173 个包中有 169 个成功下载，最终仅 `vim-common` 因累计重试耗尽而失败。

## 修复方向

### 方向 1（置信度: 中）
**重新触发 CI 构建**。这是 `repo.openeuler.org` 镜像站的临时网络波动问题（HTTP/2 流错误 + SSL 连接中断），与代码变更无关。在非高峰时段重试构建，大概率可成功通过。若多次重试仍失败，则需排查是否是 openEuler 24.03-LTS-SP4 aarch64 仓库本身存在持续性服务问题。

### 方向 2（置信度: 低）
**在 Dockerfile 中为 yum 添加重试机制**。可在 `yum install` 前设置 `yum.conf` 的重试参数（`retries`、`timeout`），或在外层用 shell 循环对 `yum install` 命令本身做重试，以增强对仓库网络波动的容错能力。但这不是根本解决方案，因为上游仓库的网络稳定性应由基础设施侧保障。

## 需要进一步确认的点
1. 确认 `repo.openeuler.org` 在构建时段（2026-07-09 13:44 UTC 左右）的 aarch64 仓库是否存在已知的服务降级或维护事件。
2. 确认同一时段其他使用 openEuler 24.03-LTS-SP4 aarch64 的 PR 是否也出现了类似的 yum 下载失败，以判断问题影响范围是全局性的还是仅该构建节点。
3. 若重试后仍然失败，需要检查 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 在 `repo.openeuler.org` 上是否实际存在且可正常访问。
