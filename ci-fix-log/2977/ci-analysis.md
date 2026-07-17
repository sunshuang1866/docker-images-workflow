# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, No more mirrors to try, aarch64

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`repo.openeuler.org` 仓库服务器的 HTTP/2 连接反复出现流层错误（`INTERNAL_ERROR`）和 SSL 读取错误，导致 vim-common 等多个 RPM 包下载失败，yum 重试所有镜像后仍无法完成下载。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 仅新增了一个标准的 Dockerfile（安装构建依赖 → clone 源码 → cmake 编译），Dockerfile 内容本身没有语法错误或逻辑问题。失败纯粹由 `repo.openeuler.org` 在构建时段（2026-07-09 13:45 UTC）的 HTTP/2 服务不稳定导致 aarch64 包下载中断，属于 CI 基础设施/上游仓库网络问题。

## 修复方向

### 方向 1（置信度: 高）
此失败为基础设施问题（`repo.openeuler.org` HTTP/2 服务不稳定），与 PR 代码无关。建议：
- 等待上游仓库恢复后重新触发 CI 构建（retry）
- 若该仓库持续不稳定，可考虑在 `yum install` 命令中为 curl/yum 添加重试机制（如配置 `retries` 和 `timeout` 参数）
- 或切换至备用镜像源

## 需要进一步确认的点
- `repo.openeuler.org` 在 2026-07-09 13:45 UTC 时段是否存在已知的 CDN/HTTP2 服务故障
- x86_64 架构的构建 job（如存在）是否同样受影响，可辅助判断问题范围
- 该失败是否为偶发（建议 retry 一次确认）
