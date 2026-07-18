# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), Stream error in the HTTP/2 framing layer, SSL_ERROR_SYSCALL, No more mirrors to try, vim-common

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: aarch64 CI runner 在从 `repo.openeuler.org` 下载 RPM 包（`gcc`、`kernel-headers`、`perl-MIME-Base64`、`vim-common`）时遭遇多次 HTTP/2 流错误（Curl error 92）和 SSL 连接中断（Curl error 56），最终 `vim-common` 下载失败导致 yum 事务中止。这些错误均为 openEuler 软件源侧的瞬时网络/协议层问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 新增了一个标准的 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`），其中 `RUN yum install -y ...` 安装编译依赖是合理且必要的步骤。失败发生在 yum 从上游仓库下载 RPM 包的过程中，多个关键包（gcc、kernel-headers、vim-common 等）因 `repo.openeuler.org` 的 HTTP/2 连接异常而下载失败。**该失败与 PR 代码逻辑无关**，Dockerfile 本身的语法和依赖声明均正确（同类已存在的 `24.03-lts-sp3` 版本的 Dockerfile 结构完全一致且构建成功）。若软件源恢复正常，该构建应可正常通过。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。根因是 openEuler 软件源 `repo.openeuler.org` 在 aarch64 CI runner 构建期间的瞬时网络不稳定（HTTP/2 流异常关闭、SSL 读取失败）。此类镜像站波动通常为临时性问题，在当前时刻重新触发 CI 大概率可正常通过。无需修改任何代码、Dockerfile 或元数据文件。

## 需要进一步确认的点
- 无。日志已明确显示失败为软件源侧的网络层协议错误（Curl error 92 / Curl error 56），与 PR 变更无因果关联。
