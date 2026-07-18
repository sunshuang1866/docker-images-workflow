# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库网络下载失败
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（yum install 步骤）
- 失败原因: aarch64 CI runner 从 `repo.openeuler.org` 下载 RPM 包时遇到多次 HTTP/2 流错误（Curl error 92）和 SSL 读取失败（Curl error 56），yum 对大部分失败的包重试成功，但 `vim-common-9.0.2092-36.oe2403sp4.aarch64` 耗尽所有镜像重试后仍失败，导致整个 yum install 命令以退出码 1 终止。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 brpc 1.16.0 Dockerfile（安装依赖 → git clone → cmake 构建），Dockerfile 中的 `yum install` 命令语法正确、包名有效。失败由构建时 `repo.openeuler.org` 的网络不稳定导致，是 CI 基础设施层面的瞬态问题。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。该失败是 openEuler 官方镜像仓库（`repo.openeuler.org`）的临时网络波动导致的 RPM 包下载失败。同一构建中大部分受影响的包（gcc、kernel-headers、perl-MIME-Base64）在 yum 自动重试后均下载成功，仅 vim-common 在重试阶段也未恢复。重新触发 CI 构建有较大概率自然通过。

### 方向 2（置信度: 低）
若重试后仍然失败，可在 Dockerfile 的 yum install 步骤中增加网络重试配置（如设置 `retries=10`、`timeout=120` 或使用 `--setopt=retries=10`），提高对网络波动的容忍度。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库在当前时间点的网络可达性是否正常
- 确认该 runner（`ecs-build-docker-aarch64-04-sp`）与其他 openEuler 镜像仓库节点的网络连接状态
- 若该问题在多次重试后持续出现，需排查是否 openEuler 24.03-LTS-SP4 aarch64 仓库端的 HTTP/2 服务存在问题
