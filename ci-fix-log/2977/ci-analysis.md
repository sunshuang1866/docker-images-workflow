# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库网络不稳定
- 新模式症状关键词: Curl error, HTTP/2 stream, Stream error, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum install, aarch64

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: CI 在 aarch64 runner 上构建镜像时，`yum install` 从 `repo.openeuler.org` 下载 RPM 包过程中频繁遭遇 HTTP/2 流错误（curl error 92）和 SSL 读取错误（curl error 56）。前 3 个受影响的包（gcc、kernel-headers、perl-MIME-Base64）通过重试恢复成功，但最后一个包 `vim-common`（即第 173/173 个包）重试仍失败，所有镜像源均已尝试无果，导致 yum 事务失败退出。失败与 PR 代码变更**无关**。

### 与 PR 变更的关联
**无关**。该 PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `yum install` 包列表和 `cmake` 构建参数语法均正确，失败完全由 aarch64 架构的 openEuler SP4 软件仓库（`repo.openeuler.org`）网络不稳定导致 RPM 包下载中断。

## 修复方向

### 方向 1（置信度: 高）
**重试触发 CI**：该失败为临时性网络基础设施问题，与代码无关。等待 openEuler SP4 aarch64 仓库服务恢复后，重新触发 CI 构建即可通过。无需修改任何文件。

### 方向 2（置信度: 低，不推荐）
若网络问题持续频发，可在 Dockerfile 的 `yum install` 命令前添加重试逻辑（如 `yum install --setopt=retries=10 --setopt=timeout=30 ...` 或包裹在 `for i in 1 2 3; do yum install ... && break; done` 循环中），但这属于 CI 平台层面的环境问题，不应在应用 Dockerfile 中引入。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库当前服务状态是否正常（可手动 curl 测试具体 RPM 包 URL）
- 确认该失败是否为偶发（retry CI 后是否通过），如果频繁复现，需联系 openEuler 镜像站运维排查 CDN/HTTP/2 层问题
