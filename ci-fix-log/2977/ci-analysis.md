# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: yum仓库网络不稳定
- 新模式症状关键词: Curl error (92), Curl error (56), Stream error in the HTTP/2 framing layer, No more mirrors to try, yum install, repo.openeuler.org

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
- 失败位置: `Dockerfile:4-11`（`RUN yum install -y` 步骤）
- 失败原因: `repo.openeuler.org` 在向 aarch64 runner 提供 openEuler 24.03-LTS-SP4 仓库 RPM 包下载时，发生了多次 Curl 网络层错误（HTTP/2 流异常中断、SSL 读取失败）。其中 gcc、kernel-headers、perl-MIME-Base64 三个包在重试后成功下载，但 `vim-common` 在耗尽所有镜像重试次数后仍下载失败，导致整个 `yum install` 命令以 exit code 1 终止。

### 与 PR 变更的关联
本次 PR 的变更完全无关。PR 仅新增了一个合法的 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 内容与已有的 SP3 版本结构一致，包依赖声明也无误。失败根本原因是构建时 `repo.openeuler.org` 的 aarch64 仓库出现网络不稳定，属于 CI 基础设施侧问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。此失败为 `repo.openeuler.org` 仓库在构建时段的临时网络不稳定所致，yum 重试机制已成功恢复 3/4 的失败包。重新触发 CI 构建大概率可以成功通过。这是一种 `infra-error`，Code Fixer 无需对 PR 代码做任何修改。

### 方向 2（置信度: 低）
若重试多次仍失败，可能表明 `repo.openeuler.org` 的 aarch64 仓库 HTTP/2 配置存在持续性问题。此时可考虑在 Dockerfile 的 `yum install` 前为 curl/libcurl 配置 `--http1.1` 降级（通过 `echo "http2=0" >> /etc/dnf/dnf.conf` 或等效方式），绕过 HTTP/2 协议层问题。但这是绕行方案，不解决上游仓库的根因。

## 需要进一步确认的点
无。日志证据充分，4 次独立的 Curl 错误（错误码 92 和 56）均指向 `repo.openeuler.org` 的网络层问题，与 PR 代码变更无任何关联。
