# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库网络抖动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum install

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
- 失败位置: Dockerfile:4（`RUN yum install -y ...` 步骤）
- 失败原因: CI 构建在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `yum install` 时，`repo.openeuler.org` 仓库多次出现 HTTP/2 流错误（Curl error 92）和 SSL 连接中断（Curl error 56），导致多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载失败，最终 vim-common 包在所有镜像尝试均告失败后触发构建终止。

### 与 PR 变更的关联
**与 PR 无关**。该 PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、README 条目、image-info 条目和 meta.yml 记录。`yum install` 命令中的包列表（git、gcc、gcc-c++、make、cmake、openssl-devel、gflags-devel、protobuf-devel、leveldb-devel、snappy-devel）均为标准系统包，与同镜像其他版本 Dockerfile（如 24.03-lts-sp3）中使用的包列表一致。失败纯因 openEuler 官方仓库 `repo.openeuler.org` 在 CI 构建时段出现网络不稳定。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。此为 `infra-error`（CI 基础设施问题），`repo.openeuler.org` 仓库的网络/HTTP/2 服务在构建时段出现间歇性故障。PR 代码本身无问题，重试 CI 极大概率通过。Code Fixer 无需修改任何代码。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段是否存在已知服务中断或网络波动（可检查 openEuler 基础设施状态页面）
- 确认该 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）与 `repo.openeuler.org` 之间的网络链路是否稳定
- 若多次重试均失败，考虑在 Dockerfile 的 `yum install` 前添加重试机制（如 `yum install --retries 5`）或使用镜像站替代

## 修复验证要求
无需验证。此为 infra-error，Code Fixer 无需执行任何代码修改。
