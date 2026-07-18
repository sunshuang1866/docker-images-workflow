# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2下载失败
- 新模式症状关键词: Curl error (92), Stream error, HTTP/2 framing, repo.openeuler.org, yum install, aarch64, No more mirrors to try

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
- 失败原因: openEuler 24.03-LTS-SP4 官方软件源 `repo.openeuler.org` 在 aarch64 架构上出现 HTTP/2 传输层不稳定（`INTERNAL_ERROR (err 2)` 及 `SSL_ERROR_SYSCALL`），导致 `gcc`、`kernel-headers`、`perl-MIME-Base64`、`vim-common` 等多个 RPM 包下载反复失败，`vim-common` 最终用尽所有镜像重试后仍无法下载，`yum` 退出码为 1，Docker 构建中断。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 新增的 Dockerfile 内容本身正确——依赖列表完整、CMake 参数合理、构建步骤清晰。失败发生在纯网络下载阶段（`yum install` 从远程仓库拉取 RPM 包），是 openEuler 官方软件源 HTTP/2 服务端的临时不稳定导致，属于 CI 基础设施问题。PR 变更中没有任何内容会触发或加剧此类网络问题。

## 修复方向

### 方向 1（置信度: 高）
**CI 基础设施重试即可。** 该失败是 `repo.openeuler.org` 的 HTTP/2 连接层瞬时不稳定所致（`INTERNAL_ERROR` 和 `SSL_ERROR_SYSCALL` 均为网络层瞬时故障标志），与 PR 代码完全无关。最可能的修复方式是等待源站恢复后**重新触发 CI 构建**（retry/rerun）。若反复重试后仍持续失败，则需 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 反向代理或 CDN 节点的稳定性问题。

## 需要进一步确认的点
- 若多次重试 CI 仍然失败，需要确认 `repo.openeuler.org` 在 aarch64 架构上的 HTTP/2 服务是否存在持续性故障。
- 需要确认该 CI 节点的网络环境是否有代理或防火墙干扰 HTTP/2 长连接（可在 CI 环境中执行 `curl -v --http2 https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/` 验证连通性）。

## 修复验证要求
无需修复验证——此失败为 infra-error，Code Fixer 无需处理任何代码变更。
