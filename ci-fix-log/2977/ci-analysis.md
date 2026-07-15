# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: yum 仓库下载网络故障
- 新模式症状关键词: Curl error, HTTP/2 framing layer, No more mirrors to try, yum install, repo.openeuler.org, aarch64

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
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `yum install` 时，`repo.openeuler.org` 源多次出现 HTTP/2 流层中断（Curl error 92）和 SSL 读取失败（Curl error 56），`vim-common` 包在所有镜像重试耗尽后仍无法下载，导致构建失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 新增的 Dockerfile 内容（包列表、构建命令）本身语法正确、逻辑合理。失败是 CI 构建环境从 `repo.openeuler.org` 下载 RPM 包时遇到的**临时性网络故障**，属于基础设施问题。日志中多次出现的 `[MIRROR]` 标签表明 yum 尝试了多个镜像源重试但仍失败。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 即可。** 该失败是 aarch64 构建节点与 `repo.openeuler.org` 之间的临时性网络波动（HTTP/2 流异常断开）。多次 Curl error (92) "HTTP/2 stream was not closed cleanly: INTERNAL_ERROR" 是典型的服务端或中间网络设备主动断开连接的信号。等网络恢复后重新触发 CI 构建，大概率可以通过。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在当时是否经历了服务端故障或维护（HTTP/2 INTERNAL_ERROR 可能是服务端问题）。
- 确认 CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否稳定。如果此类问题频繁出现，可考虑在 Dockerfile 中添加 `--retries 5` 或配置备用 yum 镜像源（如 `mirrors.huaweicloud.com` 或 `mirrors.tuna.tsinghua.edu.cn`）以提高容错性。
