# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络波动
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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 Docker 构建时，yum 从 `repo.openeuler.org` 下载 173 个 RPM 包的过程中，多次遭遇 HTTP/2 协议层错误（`Curl error 92: INTERNAL_ERROR`）和 SSL 连接中断（`Curl error 56: SSL_ERROR_SYSCALL`）。最终 `vim-common` 包耗尽所有镜像重试仍下载失败，导致整个 yum install 步骤中断。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个合法的 Dockerfile（安装依赖 → clone 源码 → cmake 构建 → make install），Dockerfile 语法正确，yum 包名均为 openEuler 24.03-LTS-SP4 仓库中已知存在的包。失败由 CI 构建节点的网络环境与 `repo.openeuler.org` 之间的 HTTP/2 连接不稳定导致，属于 CI 基础设施问题。重试（re-run）后极大概率通过。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，触发 CI 重试即可。** 该失败是 `repo.openeuler.org` 镜像站瞬时网络波动导致的临时性故障，PR 的 Dockerfile 本身没有问题。建议直接在 CI 中 re-run 该 job。

## 需要进一步确认的点
- 确认当前 `repo.openeuler.org` 的 aarch64 仓库是否已恢复正常（可手动 `curl -I` 测试上述报错的几个 RPM 包 URL）。
- 若多次重试均失败，需排查 CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络路由是否存在持续性问题。
