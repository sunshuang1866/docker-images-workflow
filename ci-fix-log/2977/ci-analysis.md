# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, No more mirrors to try, yum install

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
```

### 根因定位
- 失败位置: `Dockerfile:4-11`（`RUN yum install -y ...` 步骤，`vim-common` 包下载失败）
- 失败原因: CI 构建环境（aarch64 runner `ecs-build-docker-aarch64-04-sp`）从 `repo.openeuler.org` 下载 RPM 包时，仓库服务器多次出现 HTTP/2 流错误（`INTERNAL_ERROR`，curl error 92）和 SSL 连接中断（`SSL_ERROR_SYSCALL`，curl error 56）。虽然 `yum` 的重试机制对大多数包（gcc、kernel-headers、perl-MIME-Base64）恢复成功，但 `vim-common`（第 173/173 个包，即最后一个）的重试全部失败，耗尽所有镜像后报 `No more mirrors to try`，导致整个 `yum install` 步骤失败。

### 与 PR 变更的关联
**PR 变更与此次失败无关。** 该 PR 新增了一个标准的 brpc Dockerfile，其 `yum install` 命令安装的均为 openEuler 24.03-LTS-SP4 仓库中的常规开发包（git、gcc、cmake、openssl-devel 等），与已有 SP3 版本 Dockerfile 完全一致（仅基础镜像不同）。失败完全是 `repo.openeuler.org` 镜像站在该时间段的 HTTP/2 服务不稳定所致，属于 CI 基础设施问题，重新触发构建即可通过。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。此为 `repo.openeuler.org` 仓库服务器的临时性网络/HTTP/2 故障，与 PR 代码变更无关。无需修改 Dockerfile 或任何代码，等待仓库服务恢复正常后重新运行 CI 即可。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 镜像站在构建时间段是否存在已知的服务中断或 HTTP/2 协议层问题（可通过独立验证下载 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 等失败包来确认仓库当前是否恢复正常）。
