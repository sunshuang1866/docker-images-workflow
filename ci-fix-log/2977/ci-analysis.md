# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源网络连接不稳定
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:4-11（`yum install` 步骤，安装 173 个 RPM 包）
- 失败原因: CI 构建环境（aarch64 runner `ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 RPM 包时遭遇持续的 HTTP/2 帧层错误（Curl error 92: INTERNAL_ERROR）和 SSL 读取错误（Curl error 56: SSL_ERROR_SYSCALL）。部分包（gcc、kernel-headers）通过 yum 自动重试其他 mirror 后下载成功，但第 173 个包 `vim-common`（7.8 MB）重试后所有 mirror 均已用尽，最终失败。整个 `yum install` 过程耗时约 21 分钟（从 #7 198.5 开始到 #7 1310.3 结束），期间出现 4 次网络错误。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 新增的 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）结构正确，`yum install` 命令语法无误，所列 RPM 包名均有效且存在于 24.03-LTS-SP4 仓库中。失败完全由 CI runner 到 `repo.openeuler.org` 的网络连接不稳定导致，属于基础设施问题。PR 中的其他文件变更（README.md、image-info.yml、meta.yml）均为纯文档/元数据更新，不涉及构建逻辑。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 网络下载 RPM 包阶段的 HTTP/2 流错误和 SSL 连接重置是暂时性的基础设施问题，通常重试即可通过。yum 的自动重试机制已成功恢复了大部分失败的包下载（gcc、kernel-headers 的 mirror 错误被自动重试绕过），仅最后一个包耗尽全部 mirror 后失败，说明整体网络状态处于临界点。建议等待一段时间后重新提交 CI 构建任务。

### 方向 2（置信度: 低）
**Dockerfile 添加 yum 重试参数。** 在 `yum install` 命令中增加 `--retries` 或使用 `dnf` 的 `--setopt=retries=10` 等配置提高包下载重试次数，增强对网络波动的容忍度。但本次失败中 yum 的重试机制已生效（gcc 和 kernel-headers 的 mirror 错误均被恢复），且 vim-common 报 "No more mirrors to try" 说明已用尽所有可用 mirror，额外重试可能效果有限。此方向为可选优化，非必要。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI 构建时段是否有网络波动或维护窗口（日志时间戳：2026-07-09 13:44 UTC）
- 确认 aarch64 runner `ecs-build-docker-aarch64-04-sp` 的出站网络是否稳定，是否需要切换 runner 或配置本地镜像缓存
- 如果多次重试后仍失败，需排查是否 `repo.openeuler.org` 上 `vim-common-9.0.2092-36.oe2403sp4.aarch64` 文件本身存在问题（如校验和不匹配导致服务器端流中断）
