# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 系统包仓库网络故障
- 新模式症状关键词: `[MIRROR]`, `Curl error (92)`, `HTTP/2`, `INTERNAL_ERROR`, `Curl error (56)`, `SSL_ERROR_SYSCALL`, `No more mirrors to try`, `Error downloading packages`

## 根因分析

### 直接错误
```
#7 198.5 Package which-2.25-1.oe2403sp4.aarch64 is already installed.
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
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在 Docker 构建阶段通过 yum 从 `repo.openeuler.org` 下载 173 个依赖包时，多个包在下载过程中遭遇 HTTP/2 协议层错误（`Curl error (92): INTERNAL_ERROR`）和 SSL 传输中断错误（`Curl error (56): SSL_ERROR_SYSCALL`），最终 `vim-common` 包因所有镜像源均重试失败而下载失败，导致整个 `yum install` 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR #2977 仅新增了一个 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）和对应的元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中 `yum install` 的包列表语法和内容均正确。失败完全由 openEuler 官方软件仓库 `repo.openeuler.org` 在构建期间的网络/HTTP/2 协议故障引起，构建重试即可恢复。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修改，触发 CI 重试。** 这是 openEuler 软件仓库的临时性网络/协议故障，与 PR 代码变更无关。Code Fixer 无需处理任何文件。建议：
- 在 CI 平台重新触发失败的 aarch64 构建 job
- 如果反复失败，检查 `repo.openeuler.org` 的 HTTP/2 服务状态或临时将 yum 源切换为镜像站

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 HTTP/2 服务在构建时段是否有已知中断或性能降级
- 确认 aarch64 runner 节点到 `repo.openeuler.org` 的网络链路是否稳定
- 如果重试后仍持续失败，考虑在 Dockerfile 中添加 `yum install` 的重试逻辑或配置 fallback 镜像源

## 修复验证要求
无需修复验证。此失败为 infra-error，无需对代码做任何修改。
