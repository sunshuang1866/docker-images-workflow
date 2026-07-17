# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install

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
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在 `yum install` 过程中从 `repo.openeuler.org` 下载 RPM 包时遭遇多次 HTTP/2 连接中断（Curl error 92）和 SSL 传输失败（Curl error 56），虽然部分包通过重试成功下载（gcc、kernel-headers、perl-MIME-Base64），但 `vim-common` 耗尽所有镜像重试后最终失败，导致整个 `yum install` 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 Dockerfile（`yum install` 构建依赖 → `git clone` → `cmake && make`），Dockerfile 语法和包名均正确。失败完全由 `repo.openeuler.org` 在构建时段的网络不稳定（HTTP/2 连接异常断开、SSL 传输中断）导致，与代码改动无关。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是典型的 CI 基础设施网络波动问题，RPM 仓库 `repo.openeuler.org` 在特定时段返回 HTTP/2 stream error 和 SSL read failure。此类问题通常是临时的，重新运行 CI（retry）大概率可正常通过。无需修改任何代码。

### 方向 2（置信度: 低）
如果多次重试均失败（排除临时波动），可能是 openEuler 24.03-LTS-SP4 的 aarch64 仓库镜像存在持续性问题。此时可考虑在 Dockerfile 的 `yum install` 前增加 `yum-config-manager` 配置换用备用镜像站，或在 `yum install` 命令中增加重试参数。但当前日志证据不足以判断是否为持续性问题，优先按方向 1 重试。

## 需要进一步确认的点
- 如果 CI 重试后仍然失败，需确认 `repo.openeuler.org` 对应 aarch64 仓库在 CI 构建环境中是否长期不可达。
- 可以对比其他运行在相同 `aarch64-04-sp` runner 上的 PR 构建是否也出现类似 Curl error，以确认是该 runner 节点的网络问题还是上游仓库问题。

## 修复验证要求
无需修改代码，不涉及正则 patch 或外部源文件匹配。重试 CI 即可验证。
