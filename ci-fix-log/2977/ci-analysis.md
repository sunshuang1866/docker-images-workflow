# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络不稳定
- 新模式症状关键词: Curl error (92), Curl error (56), No more mirrors to try, yum install, repo.openeuler.org, HTTP/2 stream, INTERNAL_ERROR, SSL_ERROR_SYSCALL

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
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 aarch64 软件包时，多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）和 SSL 读取错误（Curl error 56: SSL_ERROR_SYSCALL），其中 `vim-common` 在所有镜像重试后仍然失败，导致整个 `yum install` 命令退出码为 1，Docker 构建中断。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `yum install` 命令语法和包名均正确（依赖解析阶段列出 173 个包并成功解析），失败纯粹发生在软件包下载阶段，是 `repo.openeuler.org` 到 aarch64 CI runner 之间的网络不稳定所致。

## 修复方向

### 方向 1（置信度: 高）
此失败属于 CI 基础设施网络问题，与代码无关。**无需 Code Fixer 介入**。建议：
- 重新触发 CI 构建（retry），网络状况改善后大概率通过
- 若持续失败，联系 openEuler 基础设施团队检查 `repo.openeuler.org` 的 aarch64 软件包分发节点是否存在 HTTP/2 协议兼容性或服务器端连接重置问题

## 需要进一步确认的点
- 确认是否为 `repo.openeuler.org` 的临时性网络波动（可通过重试验证）
- 检查同一时间段内其他 PR 的 aarch64 构建是否也遇到类似问题（判断是个例还是系统性问题）
- 检查 `ecs-build-docker-aarch64-04-sp` runner 的网络出口是否有带宽/连接数限制或代理配置异常
