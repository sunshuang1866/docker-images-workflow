# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络故障
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), Failure when receiving data, No more mirrors to try, vim-common, repo.openeuler.org

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
- 失败原因: CI 在 aarch64 runner 上构建时，`repo.openeuler.org` 镜像站存在网络不稳定问题，多个 RPM 包下载过程中出现 HTTP/2 stream 错误（Curl error 92）和 SSL 连接中断（Curl error 56），最终 `vim-common` 包耗尽所有镜像重试后下载失败，整个 yum 安装事务回滚。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）、更新了 README.md、image-info.yml 和 meta.yml，均为纯文件新增和文档更新。失败发生在 `yum install` 从 openEuler 官方仓库下载系统包阶段，这是 CI 基础设施层面的网络问题，Dockerfile 中安装的包列表（git、gcc、cmake、openssl-devel 等）与同仓库已有 SP3 版本的 Dockerfile 一致，包名本身不存在错误。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 openEuler 官方仓库 `repo.openeuler.org` 在 CI 构建时段（2026-07-09 13:45 UTC）出现的临时性网络故障。日志中 173 个包中有多个包遭遇 HTTP/2 stream error 和 SSL read error，说明仓库服务端或网络链路存在间歇性问题。建议重试 CI 构建（trigger rebuild），成功率预期很高。

### 方向 2（置信度: 低）
若多次重试仍失败，可考虑在 Dockerfile 的 yum 命令中添加 `--retries 10 --setopt=timeout=300` 等重试参数，提高对网络波动的容忍度。但这仅是一种容错优化，不是根因修复。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI 构建时段的服务状态（是否存在已知的 CDN/镜像站故障）。
- 若重试后仍失败，需排查 aarch64 runner 节点（`ecs-build-docker-aarch64-04-sp`）与 openEuler 仓库之间的网络连通性。
