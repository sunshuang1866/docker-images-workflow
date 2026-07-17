# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 包仓库网络不稳
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum

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
- 失败原因: CI 构建环境（aarch64 runner）从 `repo.openeuler.org` 下载 yum 包时遭遇 HTTP/2 协议层中断（Curl error 92: `INTERNAL_ERROR`）和 SSL 连接重置（Curl error 56），导致 173 个待安装包中的 `vim-common` 下载失败。yum 自动重试耗尽所有镜像后报 `No more mirrors to try`，整个 `yum install` 步骤以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 brpc Dockerfile（安装 gcc、cmake、openssl-devel 等构建依赖）、更新 README 表项、image-info.yml 和 meta.yml。Dockerfile 中的 `yum install` 命令语法和包名均正确（日志中可见依赖解析成功，`Dependencies resolved`，共 173 个包）。失败纯粹是 `repo.openeuler.org` 在 aarch64 构建时段出现网络不稳定所致。日志中可见前 172 个包中有部分遭遇了 Curl error 但通过重试成功下载（如 `gcc` 和 `kernel-headers` 均从 MIRROR 错误中恢复），仅 `vim-common` 重试耗尽后最终失败。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施/网络瞬时故障。直接用相同配置重试 CI 构建即可。多次 Curl error (92) HTTP/2 framing 错误和 (56) SSL 读错误指向 `repo.openeuler.org` CDN 在构建时段对 aarch64 节点的服务质量波动，非 Dockerfile 或仓库代码缺陷。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段（2026-07-09 13:45 UTC 前后）是否存在已知服务中断或 CDN 节点异常。
- 如果重试后仍以相同模式失败，需确认 openEuler 24.03-LTS-SP4 的 aarch64 仓库中 `vim-common-9.0.2092-36.oe2403sp4` 包本身是否有完整性/缓存问题。
- 该构建仅捕获到 aarch64 runner 日志。确认 x86_64 runner 是否也遇到同类问题，或仅 aarch64 节点受影响。
