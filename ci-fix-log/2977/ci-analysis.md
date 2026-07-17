# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络不稳定
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`yum install` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库 `repo.openeuler.org` 在 aarch64 构建过程中不稳定，多个 RPM 包下载遭遇 HTTP/2 流错误（Curl error 92）和 SSL 连接中断（Curl error 56），最终 `vim-common` 包在所有镜像源尝试均失败后导致 `yum install` 整体失败。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个语法正确的 Dockerfile（安装 brpc 1.16.0 的构建依赖）以及配套的 README、image-info.yml、meta.yml 元数据文件。失败原因是 openEuler 官方 RPM 镜像站在构建期间网络不稳定（HTTP/2 协议层错误），属于 CI 基础设施问题。相同的 `yum install` 命令在其他时间重试很可能成功。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，触发 CI 重试即可**。此失败为 openEuler 官方仓库 `repo.openeuler.org` 的网络瞬时故障导致，Dockerfile 本身无任何语法或逻辑错误。建议重新触发 CI 构建流水线，若多次重试仍出现相同错误，则可能存在仓库侧的持续性问题，需联系 openEuler 基础设施团队排查。

## 需要进一步确认的点
- 如果多次重试 CI 仍然失败，需要确认 `repo.openeuler.org` 的 aarch64 仓库（`/openEuler-24.03-LTS-SP4/OS/aarch64/`）是否存在持续性网络问题或 CDN 故障。
- 日志中仅显示了 aarch64 架构的构建过程，需要确认 x86_64 架构的构建是否成功。若 x86_64 成功而 aarch64 反复失败，可能表明 openEuler 镜像站的 aarch64 CDN 节点存在特定问题。
