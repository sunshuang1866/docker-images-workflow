# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库下载网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum install

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install ...` 步骤）
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在 `yum install` 下载 173 个 RPM 包过程中，`repo.openeuler.org` 仓库服务器出现多次 HTTP/2 流错误（Curl error 92）和 SSL 连接中断（Curl error 56），最终 `vim-common` 包因所有镜像尝试均失败而导致整个 `yum install` 命令返回 exit code 1。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）及配套的 README.md、image-info.yml、meta.yml 元数据文件。Dockerfile 中 `yum install` 命令的包名和语法均正确无误，失败原因是 openEuler 官方仓库 `repo.openeuler.org` 在构建时存在临时的网络/HTTP2 服务波动，属于 CI 基础设施问题。日志中 gcc 包首次下载也遇到 Curl error (92)，但重试后成功，进一步说明是仓库端的瞬时问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。该失败为 `infra-error`，是 openEuler 官方仓库在特定时间段内的网络波动导致 aarch64 RPM 包下载中断。建议触发 CI 重试（re-run），待仓库服务恢复后构建应能通过。Code Fixer 无需处理。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 仓库服务在当前时间是否已恢复正常。可以通过 `curl -I https://repo.openeuler.org` 验证连通性。
- 如果多次重试仍失败，需确认 openEuler 24.03-LTS-SP4 的 aarch64 仓库是否存在持续性的上游服务问题。
