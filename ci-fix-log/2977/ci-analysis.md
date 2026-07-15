# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站网络不稳定
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: `repo.openeuler.org` 镜像站在 aarch64 构建期间出现 HTTP/2 连接中断（Curl error 92）和 SSL 读失败（Curl error 56），导致多个 RPM 包下载过程中反复重试，最终 `vim-common` 包耗尽所有镜像重试次数而彻底失败。

### 与 PR 变更的关联
PR 变更与本次失败**无关**。PR 仅新增了 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile` 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 内容为常规的 `yum install` + `cmake` + `make` 构建流程，没有任何语法错误或逻辑问题。失败纯粹由 openEuler 官方镜像站 `repo.openeuler.org` 在 aarch64 架构运行时出现网络不稳定所致。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试构建即可。** 本失败属于 `infra-error`，根因是 `repo.openeuler.org` 镜像站网络瞬时故障，与 PR 代码变更无关。在镜像站恢复稳定后，重新触发 CI 构建即可通过。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 镜像站当前状态是否已恢复（可通过浏览器访问或 `curl -I` 测试）。
- 若同一 PR 多次重试均在同一阶段（aarch64 包下载）失败，需排查是否为镜像站对特定 IP 段（CI runner 的出口 IP）存在限流或连接限制。
