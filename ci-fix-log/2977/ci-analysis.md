# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输异常
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), Failure when receiving data, repo.openeuler.org, yum install, No more mirrors to try

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
- 失败原因: CI 构建节点在 `yum install` 下载 173 个 RPM 包时，`repo.openeuler.org` 仓库 HTTP/2 传输层出现多次异常（Curl error 92: HTTP/2 stream INTERNAL_ERROR；Curl error 56: SSL read syscall error），最终 `vim-common` 包因所有镜像源均已尝试并失败而无法下载，`yum` 退出码 1 导致 Docker 构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个标准的 Dockerfile（安装 brpc 1.16.0 依赖并编译），`yum install` 命令语法正确、包名均有效。失败根因是构建时 `repo.openeuler.org` 镜像站的 HTTP/2 传输链路不稳定——多个 RPM 包在下载过程中遇到 HTTP/2 流中断（INTERNAL_ERROR）和 SSL 连接异常（SSL_ERROR_SYSCALL）。这是 CI 基础设施侧的网络/服务器问题，不是 PR 代码变更引起的。

## 修复方向

### 方向 1（置信度: 高）
**重试构建即可。** 该失败与代码无关，属于 `repo.openeuler.org` 仓库临时性的 HTTP/2 传输故障。在仓库恢复稳定后重新触发 CI 构建（retry job）应可正常通过。无需对 Dockerfile 或任何代码文件做修改。

## 需要进一步确认的点

- 确认 `repo.openeuler.org` 的 HTTP/2 服务在构建时段是否存在已知故障或维护窗口。
- 若同类失败（HTTP/2 流错误）在多次构建中持续出现，需检查 CI aarch64 runner (`ecs-build-docker-aarch64-04-sp`) 到 `repo.openeuler.org` 的网络链路是否存在 MTU/代理/HTTP/2 兼容性问题。
- 历史上该仓库是否存在类似 HTTP/2 传输故障的已知问题记录，可确认是否为偶发还是周期性出现。
