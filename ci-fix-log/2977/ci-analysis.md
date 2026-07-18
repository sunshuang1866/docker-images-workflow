# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 stream, repo.openeuler.org, No more mirrors to try, yum install

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
- 失败位置: Dockerfile:4（`RUN yum install -y ...` 步骤）
- 失败原因: CI 构建节点（`ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 yum 包时遭遇间歇性网络故障，多个 RPM 包出现 Curl error (92) HTTP/2 流错误和 Curl error (56) SSL 读取错误。yum 对大多数失败包重试成功，但 `vim-common` 在耗尽所有镜像重试后仍失败，导致整个 yum 事务中断并返回 exit code 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准 Dockerfile（安装依赖 → 克隆源码 → cmake 构建 → make），未修改任何仓库源配置或网络相关设置。该失败是 `repo.openeuler.org` 软件源在 CI 构建期间的瞬时网络不稳定所致，属于基础设施问题。同一基础镜像（`openeuler:24.03-lts-sp4`）在其他成功运行的 CI job 中也能正常完成 yum 安装。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改。** 此为 `infra-error`，与 PR 代码变更无关。建议直接重新触发 CI 构建（retry），在新的构建周期中 `repo.openeuler.org` 大概率恢复正常，yum 包下载可顺利完成。

### 方向 2（置信度: 低）
若重试后仍持续出现同类 Curl 错误（多次重新触发均在同一阶段失败），可考虑在 Dockerfile 的 yum 步骤前添加 `yum makecache` 或对 yum 配置设置 `retries=10`、`timeout=120` 等网络容错参数。但这属于对基础设施问题的规避性处理，非根因修复。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI 失败时间点（2026-07-09 13:45 UTC 附近）是否存在已知的服务端网络波动或 CDN 异常。
- 若重试 3 次以上仍持续失败，需排查 CI runner 节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否存在持续性问题（如防火墙规则变更、代理配置等）。
