# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库网络抖动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org, yum install

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`yum install` 步骤）
- 失败原因: 在 aarch64 runner 上通过 yum 从 `repo.openeuler.org` 下载 RPM 包时，多个包遭遇 HTTP/2 流错误（Curl error 92）和 SSL 连接中断（Curl error 56），其中 `vim-common` 包在所有镜像源重试后仍下载失败，导致整个 `yum install` 命令退出。173 个包中 172 个下载成功，仅 `vim-common` 因网络问题最终失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个标准的 Dockerfile（安装 brpc 及其依赖）、更新了 README、image-info.yml 和 meta.yml。`yum install` 安装的都是 openEuler 24.03-LTS-SP4 官方仓库中的标准系统包，Dockerfile 中的包名和命令语法均正确无误。失败完全由构建时 openEuler 官方软件仓库的网络连接不稳定导致。

## 修复方向

### 方向 1（置信度: 高）
**重试即可**。这是典型的 CI 基础设施网络抖动问题。`repo.openeuler.org` 的 HTTP/2 连接在下载大文件（如 gcc 30MB、kernel-headers 1.7MB、vim-common 7.8MB）时出现了间歇性流中断。Code Fixer 无需修改任何文件——直接重新触发 CI 构建，大概率会通过。若多次重试仍失败，可考虑在 Dockerfile 的 `yum install` 命令中添加 `--retries 5` 重试参数，或在 Dockerfile 顶部添加 `RUN echo 'timeout=120' >> /etc/yum.conf` 增加下载超时时间。

## 需要进一步确认的点
- 若重新触发 CI 后仍失败，需确认 `repo.openeuler.org` 是否在当天存在服务端问题（如 CDN 节点故障、HTTP/2 负载均衡异常）。
- 确认 runner `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络路径是否稳定（多次 Curl error 92 提示 HTTP/2 协议层存在问题）。

## 修复验证要求
无。本次失败为 infra-error，无需修改代码，重新触发 CI 构建即可验证。
