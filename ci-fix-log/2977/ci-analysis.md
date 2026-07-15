# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 包仓库网络异常
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR, SSL_ERROR_SYSCALL, repo.openeuler.org, No more mirrors to try

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
- 失败原因: CI 构建环境在 aarch64 runner 上通过 `yum` 从 `repo.openeuler.org` 下载 RPM 包时，遭遇多次 HTTP/2 流错误（Curl error 92）和 SSL 读取错误（Curl error 56），属于 openEuler 软件包仓库服务端或中间网络基础设施的临时性故障。最终 `vim-common` 包在尝试所有可用镜像后仍无法下载，导致整个 `yum install` 命令失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 变更内容仅为：
- 新增 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）
- 更新 README.md、image-info.yml、meta.yml 的条目信息

Dockerfile 中的 `yum install` 语法正确，依赖包名称和来源均合理。失败完全由 openEuler 官方包仓库（`repo.openeuler.org`）在构建期间的网络服务异常所致，非 PR 代码引入的问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施的临时性问题（包仓库网络异常）。Code Fixer 无需处理，建议在 openEuler 包仓库服务恢复后重新触发 CI 构建。若多次复现同一问题，可考虑在 Dockerfile 的 `yum install` 前添加 `--retries` 相关参数或调整 yum 的 `mirrorlist` 配置使用备用镜像源。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段是否存在已知的服务中断或维护窗口。
- 若该问题在多次重试后持续复现，需确认是否需要为 openEuler 24.03-LTS-SP4 的 aarch64 runner 配置额外或备用 RPM 镜像源。
