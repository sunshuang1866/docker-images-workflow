# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库网络不稳定
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 framing layer, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, Error downloading packages, Failed to solve

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
- 失败原因: CI 构建环境中 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在通过 `yum` 从 `repo.openeuler.org` 下载 173 个 RPM 依赖包时，多次遭遇 HTTP/2 流错误（Curl error 92）和 SSL 读失败（Curl error 56），最终 `vim-common` 包下载完全失败（所有镜像源均已尝试无效），导致 `yum install` 以退出码 1 终止，Docker 构建失败。

### 与 PR 变更的关联
**与 PR 无关。** PR 仅新增了一个标准格式的 Dockerfile（使用 `yum install` 安装编译依赖）以及配套的 README、image-info.yml、meta.yml 元数据文件。Dockerfile 中 `yum install` 命令语法正确、包名均有效（依赖解析阶段列出了完整的 173 个包清单）。失败纯粹是因为 CI 构建过程中 `repo.openeuler.org` 的 aarch64 仓库发生网络波动，导致部分大型 RPM 包（如 `gcc` 30MB、`vim-common` 7.8MB）在 HTTP/2 传输层中断。日志中 `gcc` 包在重试后成功下载（步骤 34），但 `vim-common` 在最后阶段（172/173 完成后）彻底失败，明这种网络问题在本次构建中持续存在。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。这是 CI 基础设施问题（`repo.openeuler.org` 的 aarch64 仓库网络不稳定），属于 `infra-error`。建议触发重新构建（retry），网络问题通常是瞬时的，重试后大概率成功。

### 方向 2（置信度: 中）
如果多次重试仍然失败，可在 Dockerfile 的 `yum install` 命令中添加 `--retries 10 --setopt=timeout=120` 等重试/超时参数，提高 yum 对网络波动的容忍度。但此方向属于治标方案，不建议作为首选。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 aarch64 仓库在当前时间段是否存在已知的服务端 HTTP/2 或 CDN 问题。
- 确认同一时间段其他 PR 的 aarch64 构建是否也出现类似的 Curl error (92) / (56) 错误——如果是，则为上游仓库的普遍性问题。

## 修复验证要求
无需验证。此失败为 infra-error，与 PR 代码变更无关。Code Fixer 无需处理。
