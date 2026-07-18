# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 stream error, SSL_ERROR_SYSCALL, yum, repo.openeuler.org, No more mirrors to try

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（yum install 步骤）
- 失败原因: CI 构建节点在 yum 下载 RPM 包时，`repo.openeuler.org` 镜像站出现间歇性网络故障（HTTP/2 流中断、SSL 连接异常），导致 `vim-common` 等多个包下载失败，yum 耗尽所有镜像后安装终止。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 新增的 Dockerfile 内容正确——yum install 命令格式、包名、基础镜像均无误。失败发生在 Docker 构建的 yum 包下载阶段，根因是 `repo.openeuler.org` 镜像站在 aarch64 通道上出现了网络层故障。日志中 `gcc`（30 MB）、`kernel-headers`（1.7 MB）等大包也遇到了同类 Curl 错误但通过重试成功下载，而 `vim-common`（7.8 MB）在重试耗尽后仍然失败。这是 CI 基础设施/上游镜像站的瞬时性问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是纯粹的 infra-error，与 Dockerfile 正确性无关。建议在 CI 侧重试该 job（re-run），待 `repo.openeuler.org` 镜像站网络恢复后即可通过。若该问题频繁复现，可考虑在 Dockerfile 的 `yum install` 前添加 `yum makecache` 或为 yum 配置增加 `retries`/`timeout` 参数以提高容错性，但这是可选优化而非必要修复。

## 需要进一步确认的点
- `repo.openeuler.org` 24.03-LTS-SP4 aarch64 仓库是否在构建时间点存在服务端稳定性问题（可通过重试后的结果确认是否为瞬时故障）
- 若重试后仍然失败，需要确认 `vim-common-9.0.2092-36.oe2403sp4.aarch64` 该 RPM 在镜像站上是否真实存在
- 检查 CI aarch64 构建节点 `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络连接稳定性

## 修复验证要求
（无需填写——infra-error 不涉及正则 patch 或代码修改）
