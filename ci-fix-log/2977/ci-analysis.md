# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2协议错误
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
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install` 步骤）
- 失败原因: CI 在 aarch64 runner 上执行 `yum install` 时，`repo.openeuler.org` 的 HTTP/2 服务端频繁出现流关闭异常（Curl error 92: HTTP/2 stream INTERNAL_ERROR）和 SSL 连接中断（Curl error 56: SSL_ERROR_SYSCALL），导致 `vim-common` 等多个 aarch64 RPM 包下载失败。大部分包通过 yum 自动重试成功下载，但 `vim-common`（173 个包中的最后一个，7.8MB）重试耗尽后最终失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个 brpc 1.16.0 的 Dockerfile（及配套的 meta.yml、README.md、image-info.yml 文档更新）。Dockerfile 中 `yum install` 的包列表（git、gcc、gcc-c++、cmake 等）是该仓库中大量同类型镜像 Dockerfile 的标准依赖组合，语法正确。失败完全由 openEuler 官方 RPM 仓库 `repo.openeuler.org` 的 aarch64 通道 HTTP/2 服务端不稳定导致。

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重试。** 由于错误是 `repo.openeuler.org` 仓库服务端的间歇性 HTTP/2 协议问题，属于基础设施故障，PR 代码本身无需修改。触发一次重新构建（re-run），如果仓库服务恢复稳定，构建将自动通过。

### 方向 2（置信度: 低）
**在 Dockerfile 中为 yum 添加重试参数。** 在 `yum install` 命令中添加 `--setopt=retries=10` 增加重试次数，以容忍仓库的间歇性故障。但此方法治标不治本，且不能保证在仓库严重不稳定时仍能通过。

## 需要进一步确认的点
1. `repo.openeuler.org` 的 aarch64 通道在构建时段（2026-07-09 13:45 UTC 前后）是否发生过已知的服务中断或性能下降。
2. `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 在该仓库中是否存在或已损坏（可尝试直接 wget 该 URL 验证）。
3. 同一仓库中其他 SP4 镜像的 aarch64 构建是否在相同时间段也出现同类下载失败。
