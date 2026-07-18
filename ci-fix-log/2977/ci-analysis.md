# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库HTTP/2网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` RUN 步骤）
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）从 `repo.openeuler.org` 下载 RPM 包时遭遇反复的 HTTP/2 流错误（Curl error 92）和 SSL 读取错误（Curl error 56）。多数包经重试后最终成功，但 `vim-common` 包耗尽所有镜像重试后仍下载失败，导致整个 `yum install` 命令以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 语法正确，`yum install` 列出的所有依赖包名称均为 openEuler 24.03-LTS-SP4 仓库中真实存在的合法包。本次失败是 CI 构建节点与 `repo.openeuler.org` 之间的网络层 / HTTP/2 协议层不稳定所致，属于基础设施问题。同一 PR 在 x86-64 架构 runner 上应可正常通过（PR diff 中无架构限制性约束）。

## 修复方向

### 方向 1（置信度: 高）
此为 `infra-error`，**Code Fixer 无需处理**。建议触发 CI 重试（re-run / re-trigger），在网络状况良好的时段让构建重跑。aarch64 runner 到 `repo.openeuler.org` 的网络波动属于临时性基础设施问题，不涉及任何代码层面的修复。

### 方向 2（置信度: 低）
若反复重试仍失败（极为罕见），可考虑在 Dockerfile 的 `yum install` 命令前增加 `echo 'retries=10' >> /etc/yum.conf` 或 `echo 'timeout=300' >> /etc/yum.conf` 提高 yum 的网络容忍度。但鉴于这是新增 Dockerfile，应尽量保持与原 24.03-lts-sp3 版本的写法一致，此方向仅作为兜底参考。

## 需要进一步确认的点
- 确认 x86-64 runner 上该 PR 的构建是否通过（从日志看仅提供了 aarch64 runner 的日志，x86-64 runner 的状态未知，但根据 PR diff 推断 x86-64 构建应不受影响）。
- 确认 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 仓库在 CI 构建时段是否存在已知的服务端问题。

## 修复验证要求
不适用（infra-error，无需代码修复）。
