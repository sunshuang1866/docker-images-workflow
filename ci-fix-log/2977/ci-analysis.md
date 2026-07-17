# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源HTTP/2传输中断
- 新模式症状关键词: Curl error (92), HTTP/2, INTERNAL_ERROR, repo.openeuler.org, No more mirrors to try, yum install, SSL_ERROR_SYSCALL

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（yum install 步骤）
- 失败原因: CI aarch64 runner 从 `repo.openeuler.org` 下载 RPM 包时，多个包遭遇 HTTP/2 协议层中断（Curl error 92: INTERNAL_ERROR）和 SSL 连接异常（Curl error 56），其中 `vim-common` 重试耗尽所有镜像后仍失败，导致 yum install 整体失败。

### 与 PR 变更的关联
**无关。** PR 新增的 Dockerfile 语法正确，yum install 命令中的包名均有效（yum 成功解析依赖并列出 173 个待安装包，其中 172 个成功下载）。失败由 `repo.openeuler.org` 镜像站在构建期间（2026-07-09 13:45-14:10 UTC）的 HTTP/2 传输不稳定导致，与 PR 代码变更无关。重试大概率可通过。

## 修复方向

### 方向 1（置信度: 高）
此失败为 CI 基础设施网络波动，无需修改 Dockerfile 或任何代码。**直接重新触发 CI 构建即可**，等待 openEuler 仓库源恢复稳定后自然通过。历史上大量成功构建的 aarch64 镜像均可证明该仓库源通常可靠。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 aarch64 节点上的网络连接状态是否已恢复（可通过单独 curl 测试 `https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 验证）
- 如果反复重试仍失败，可检查 yum 配置中是否可添加额外的备用镜像源（如华为云镜像站），降低单点网络波动影响
