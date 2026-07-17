# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库下载网络故障
- 新模式症状关键词: Curl error, HTTP/2 framing layer, Stream error, INTERNAL_ERROR, SSL_ERROR_SYSCALL, yum install, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: CI 构建节点（`ecs-build-docker-aarch64-04-sp`，aarch64 架构）在从 `repo.openeuler.org` 下载 RPM 包时遭遇多次 HTTP/2 协议层错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接重置（Curl error 56: SSL_ERROR_SYSCALL），多个软件包（gcc、kernel-headers、perl-MIME-Base64、vim-common）均受影响。yum 对此类瞬态错误有一定重试能力（gcc 和 kernel-headers 最终下载成功），但 vim-common 在重试耗尽所有 mirror 后仍失败，导致整个 `yum install` 命令以退出码 1 终止。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 新增的 Dockerfile 内容（`yum install` 包列表、cmake 配置参数）语法正确且包名均有效——日志显示 yum 成功解析了全部 173 个待安装包的依赖关系树并进入了下载阶段。失败纯粹是因为 aarch64 runner 与 `repo.openeuler.org` 之间的网络链路不稳定，172/173 个包成功下载（尽管有多个经历了重试），仅最后一个包 `vim-common` 重试耗尽后失败。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是典型的网络瞬时故障（HTTP/2 stream reset、SSL read syscall error），日志中 173 个包中有 169 个最终成功下载，且部分失败的包（如 gcc、kernel-headers）在重试后也成功。当前故障无代码层面的修复点，最可能的解决方案是等待网络恢复后重新触发同一 PR 的 CI 流水线。如果多次重试均在同一包上失败，则需排查 `repo.openeuler.org` 是否对特定 aarch64 软件包存在 CDN 缓存问题。

### 方向 2（置信度: 低）
**添加 yum 重试机制。** 如果 openEuler 仓库的网络不稳定是持续性现象，可在 Dockerfile 的 `yum install` 前增加 `yum-config-manager` 设置（如增大 `retries` 和 `timeout` 参数），或在 `RUN` 中包裹重试循环。但此方向属于"治标不治本"，且当前仅发生一次，需观察是否需要长期方案。

## 需要进一步确认的点
1. 该故障是否为孤立事件：可查看同时间段内其他使用 `repo.openeuler.org` 的 CI job 是否也遇到类似的 HTTP/2 stream error。
2. 换用 x86_64 runner 构建同一 Dockerfile 是否也失败——日志仅为 aarch64 runner 的构建记录，若 x86_64 构建成功则可进一步确认为 aarch64 仓库 CDN 节点的瞬时故障。
3. `repo.openeuler.org` 的 aarch64 软件包仓库是否存在 HTTP/2 协议兼容性问题——多次出现的 `INTERNAL_ERROR (err 2)` 暗示服务器端 HTTP/2 流管理可能存在 bug 或配置问题，可联系 openEuler Infra 团队排查。
