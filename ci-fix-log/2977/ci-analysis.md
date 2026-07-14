# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Yum镜像网络波动
- 新模式症状关键词: Curl error (92), HTTP/2, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
- 失败原因: openEuler 官方仓库 `repo.openeuler.org` 在 CI 构建期间（aarch64 runner `ecs-build-docker-aarch64-04-sp`）发生间歇性 HTTP/2 连接中断和 SSL 连接重置，导致 173 个待安装 RPM 包中有 4 个（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载失败。前三者经 yum 自动重试后成功下载，但 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 耗尽所有重试后仍未成功，导致整个 `yum install` 步骤失败。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 仅新增了一个标准的 Dockerfile（安装依赖 → clone 源码 → cmake 构建）和配套的元数据/文档文件。Dockerfile 的 `yum install` 命令语法正确，依赖包列表合理（与同类 brpc Dockerfile 一致）。失败纯粹由 openEuler 官方仓库在构建时刻的网络不稳定导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建即可。** 这是 openEuler 官方仓库 `repo.openeuler.org` 的临时网络抖动，与代码无关。Code Fixer 无需修改任何文件。建议直接重新触发 CI 流水线，等待仓库网络恢复正常后构建自然通过。

## 需要进一步确认的点
- 无需进一步确认。日志中 4 个包的 Curl error 明确指向 `repo.openeuler.org` 的 HTTP/2 层间歇性故障，与 PR 代码变更无任何关联。
