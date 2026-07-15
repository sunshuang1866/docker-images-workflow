# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, SSL_ERROR_SYSCALL, No more mirrors to try, Error downloading packages

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（yum install 步骤）
- 失败原因: 在 aarch64 构建节点上，`repo.openeuler.org` 镜像站的 HTTP/2 连接反复出现流错误（INTERNAL_ERROR）和 SSL 读取失败（SSL_ERROR_SYSCALL），导致多个 RPM 包的下载被中断。虽然 yum 对部分包（如 gcc、kernel-headers、perl-MIME-Base64）自动重试成功，但 `vim-common` 包耗尽所有镜像重试后仍无法完成下载，yum 事务整体失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件，Dockerfile 中的 `yum install` 命令格式规范、包名正确。失败完全由 openEuler 官方软件源 `repo.openeuler.org` 在 aarch64 构建节点上的网络/协议不稳定导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。这是典型的中间节点网络抖动或镜像站临场波动导致的瞬时故障。无需修改任何代码或 Dockerfile，直接重新触发 CI 构建即可。由于网络问题具有间歇性，多数情况下重试后可成功下载缺失的包。

### 方向 2（置信度: 中）
若重试多次仍持续失败，可在 Dockerfile 的 yum 命令前添加重试机制，例如为 yum 配置 `retries` 和 `timeout` 参数，或先用 `yum makecache` 预热元数据缓存后再执行安装。但这属于防御性加固，不应是首次修复的首选方案。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI 运行时段的服务状态是否正常（是否有维护或过载）
- 确认该 aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否稳定
- 观察同批次其他应用的 SP4 镜像构建是否也遭遇了相同的 HTTP/2 流错误，以判断是单点故障还是镜像站整体问题
