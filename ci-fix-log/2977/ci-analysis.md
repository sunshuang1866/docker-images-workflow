# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络抖动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（yum install 步骤）
- 失败原因: CI aarch64 构建节点在 `yum install` 从 `repo.openeuler.org` 下载 173 个 RPM 包的过程中，`repo.openeuler.org` 仓库服务器出现持续的 HTTP/2 连接异常（INTERNAL_ERROR）和 SSL 读错误，导致多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common 等）下载失败。`vim-common` 在所有镜像均尝试后最终失败，yum 整体退出码为 1，构建中断。

### 与 PR 变更的关联
**与 PR 无关。** PR 变更仅新增了一个全新的 Dockerfile（brpc 1.16.0 on openEuler 24.03-LTS-SP4），其中 `yum install` 命令语法正确、包名均为 openEuler 24.03-LTS-SP4 有效包。失败完全由构建期间 `repo.openeuler.org` 仓库服务器的网络不稳定引起，属于 CI 基础设施问题。重试相同的构建有很大概率成功。

## 修复方向

### 方向 1（置信度: 高）
无需修改 PR 代码。此为 CI 构建节点的网络/仓库源临时故障，建议触发 re-run / re-trigger 该 job。如果该镜像频繁因网络问题失败，可考虑在 Dockerfile 的 yum install 前添加 `--retries` 或为 repo 源增加备用镜像站配置，但这属于优化而非本次 PR 的问题。

## 需要进一步确认的点
- 确认 amd64 架构的构建 job 是否同样因网络问题失败（本次日志仅包含 aarch64 runner 的输出）。如果 amd64 通过了，进一步确认 aarch64 失败确实是该 runner 当时网络偶发问题。
- 确认 `repo.openeuler.org` 在构建时段是否有已知的服务中断或网络波动。

## 修复验证要求
无需验证。本次失败与代码变更无关，Code Fixer 无需执行任何代码修改。
