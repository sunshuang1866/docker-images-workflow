# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件仓库网络不稳定
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), Failure when receiving data, No more mirrors to try, repo.openeuler.org, yum install, aarch64

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install` 步骤）
- 失败原因: CI aarch64 runner (`ecs-build-docker-aarch64-04-sp`) 在 `yum install` 阶段从 `repo.openeuler.org` 下载 RPM 包时，遭遇多次 HTTP/2 帧层错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接中断（Curl error 56: SSL_ERROR_SYSCALL）。`yum` 的重试机制用尽了所有可用镜像站，最终在下载 `vim-common` 时报 `No more mirrors to try` 而失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 此 PR 的改动为纯增量内容——新增一个 Dockerfile 及配套的 README.md、image-info.yml、meta.yml 条目，用于在 openEuler 24.03-LTS-SP4 上构建 brpc 1.16.0 镜像。Dockerfile 中使用的 `yum install` 命令与同级目录下 SP3 版本及其他镜像 Dockerfile 的模式完全一致。错误直接来自 `repo.openeuler.org` 软件仓库的网络传输层，属于 CI 基础设施的临时性网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，触发 CI 重试。** 这是 `repo.openeuler.org` 软件仓库在本次构建时段的临时网络不稳定，表现为 HTTP/2 流异常中断和 SSL 连接丢失。Code Fixer 无需对任何文件做修改，直接重新触发 CI 运行（或等待镜像站恢复后自动重试）即可。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在当前时段对 aarch64 runner 的网络连通性是否已恢复（可查看该时段的镜像站状态页面或运维公告）。
- 如果重试后仍出现相同错误，建议排查 CI runner 节点的网络出口是否对 `repo.openeuler.org` 存在间歇性丢包或 HTTP/2 协议兼容性问题。

## 修复验证要求
不适用——此失败为 infra-error，无需修改任何正则或代码。
