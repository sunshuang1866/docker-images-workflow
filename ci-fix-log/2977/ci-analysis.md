# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像站网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
- 失败原因: CI 构建节点（aarch64 runner `ecs-build-docker-aarch64-04-sp`）在通过 `yum` 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时，遭遇 `repo.openeuler.org` 镜像站网络不稳定，多个包出现 HTTP/2 协议层错误（Curl error 92: Stream error / INTERNAL_ERROR）和 SSL 连接中断（Curl error 56: SSL_ERROR_SYSCALL），最终 `vim-common` 包在所有镜像重试后仍无法下载，导致 `yum install` 失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile（安装构建依赖 → 克隆源码 → cmake/make 编译），Dockerfile 中的 `yum install` 命令语法正确、包名全部有效（yum 依赖解析器成功解析出 173 个待安装包）。失败完全由 `repo.openeuler.org` 镜像站在构建时段（2026-07-09 13:44 UTC 前后）的网络不稳定导致，构建节点到镜像站的 HTTP/2 连接反复出现协议层错误。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改，重新触发 CI 构建。** 这是 `repo.openeuler.org` 镜像站临时的网络波动/服务端 HTTP/2 协议层异常导致的 `infra-error`。镜像站恢复后，重新触发该 PR 的 CI 流水线即可通过。Code Fixer 无需处理。

## 需要进一步确认的点
- `repo.openeuler.org` 在构建时段（2026-07-09 13:44–14:07 UTC）是否存在已知的服务端 HTTP/2 协议缺陷或网络中断。
- 如果该问题在多次重试后持续复现，需检查 aarch64 构建节点到 `repo.openeuler.org` 的网络连接稳定性（可能与特定 CDN 节点或网络路径有关），可尝试在 Dockerfile 的 `yum install` 前添加 `yum-config-manager` 配置或重试逻辑以增强容错性。
