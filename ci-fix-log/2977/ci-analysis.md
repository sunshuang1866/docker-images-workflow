# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 软件源网络不稳定
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 198.5  perl-Error                     noarch   1:0.17029-4.oe2403sp4       OS           27 k
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1018.0 (77/173): perl-Error-0.17029-4.oe2403sp4.noarch  60 kB/s |  27 kB     00:00
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile` 中的 `yum install` 步骤
- 失败原因: `repo.openeuler.org` 软件源网络不稳定，导致 `vim-common` 等 aarch64 RPM 包下载失败（HTTP/2 协议层传输中断、SSL 读取失败）。173 个包中 172 个下载成功或重试恢复，仅 `vim-common` 在所有镜像源重试后仍失败。

### 与 PR 变更的关联
此失败与 PR 变更无关。PR 仅新增了 Dockerfile 及 README/image-info.yml/meta.yml 等描述文件，Dockerfile 中的 `yum install` 命令本身语法正确（在同仓库其他 openEuler SP4 Dockerfile 中广泛使用）。根本原因是 CI 运行期间 `repo.openeuler.org` 的 aarch64 软件源出现网络抖动，多包下载出现 HTTP/2 帧错误（Curl error 92）和 SSL 读取失败（Curl error 56），属于 CI 基础设施问题，不是代码错误。

## 修复方向

### 方向 1（置信度: 中）
此为 CI 基础设施问题（`infra-error`），Code Fixer 无需处理。建议重新触发 CI 构建，在 `repo.openeuler.org` 网络恢复后大概率能通过。若反复出现同类问题，可在 Dockerfile 的 `yum install` 前增加 `yum makecache` 或添加 `--retries` 等重试参数来增强容错能力。

## 需要进一步确认的点
- `repo.openeuler.org` 在 aarch64 架构镜像源在 CI 构建时间段是否存在已知网络故障或维护窗口。
- 若重试后仍失败，需确认 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 在源上是否已损坏或下架。
