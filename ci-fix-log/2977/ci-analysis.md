# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, repo.openeuler.org, yum install, No more mirrors to try

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
ERROR: failed to solve: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install -y ...` 步骤）
- 失败原因: CI aarch64 runner 在通过 `yum` 从 `repo.openeuler.org` 下载依赖包时，遭遇多次 HTTP/2 帧层错误（Curl error 92）和 SSL 读取错误（Curl error 56），最终 `vim-common` 包在所有镜像源重试失败后导致整个安装步骤中断。这不是代码问题，而是 openEuler 官方仓库的网络/服务端基础设施问题。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 新增的 Dockerfile 语法正确、依赖声明完整。失败纯粹是因为 CI 构建环境的 aarch64 节点在下载 `repo.openeuler.org` 上的 RPM 包时遇到服务器端 HTTP/2 协议层错误。日志中可见 `gcc` 和 `kernel-headers` 同样遭遇 Curl error (92)，但通过镜像重试侥幸成功；`vim-common` 则重试耗尽后失败（`No more mirrors to try`），导致整个 yum 事务回滚。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是一个 transient（暂时性）的 CI 基础设施问题。`repo.openeuler.org` 的 HTTP/2 服务端存在间歇性帧错误（`INTERNAL_ERROR`）和 SSL 连接中断（`SSL_ERROR_SYSCALL`）。建议重新触发 CI 构建（retry），大部分情况下网络恢复后即可通过。这个错误与 openEuler 仓库服务器的健康状况相关，不受 PR 代码控制。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在当时是否存在服务端 HTTP/2 或 SSL 层面的已知问题。
- 如果多次重试仍然失败，可能需要检查是否 `repo.openeuler.org` 对来自 CI runner 的并发请求有速率限制或 HTTP/2 连接数限制。
- 检查是否可以配置 yum/DNF 的 `retries` 和 `timeout` 参数以增强对这类暂时性网络错误的容错能力（属于 CI 基础设施配置，非本 PR 范围）。
