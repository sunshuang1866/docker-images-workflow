# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站网络不稳定
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, repo.openeuler.org, No more mirrors to try

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（yum install RUN 指令）
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在通过 `yum install` 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时，遇到多次 HTTP/2 协议层流错误（Curl error 92）和 SSL 读取系统调用失败（Curl error 56），最终 `vim-common` 包的下载在所有镜像源均失败，yum 整体安装步骤以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 新增了一个标准的 brpc Dockerfile，其 `yum install` 命令列出的软件包名正确、格式规范。失败的直接原因是 CI 构建节点到 `repo.openeuler.org` 之间网络不稳定，导致大量 HTTP/2 stream 未正常关闭及 SSL 连接中断，属于 CI 基础设施问题。日志显示多个包（gcc、kernel-headers、perl-MIME-Base64、vim-common）均遭遇了相同的网络错误，且构建节点为 aarch64 专用 runner，进一步佐证这是该节点与镜像源之间的网络连接质量问题。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建。该失败为 `repo.openeuler.org` 镜像站与 CI 构建节点之间的**瞬时网络故障**，与 PR 的 Dockerfile 内容无关。多次 HTTP/2 stream error 和 SSL_ERROR_SYSCALL 是典型的网络层间歇性中断，通常在网络恢复后重试即可通过。建议直接 `/retest` 或重新触发 CI pipeline，无需修改任何文件。

## 需要进一步确认的点
- 若多次重试后仍然失败，需检查 CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的出网连通性，可能存在防火墙、代理或 DNS 配置问题。
- 可对比 x86_64 runner 上同 PR 的构建结果，确认是否为 aarch64 节点专属的网络问题。

## 修复验证要求（仅当修复涉及正则 patch 外部源文件时填写）
不适用。本失败为 infra-error，无需代码修复。
