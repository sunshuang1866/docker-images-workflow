# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Yum 仓库下载网络错误
- 新模式症状关键词: Curl error (92), HTTP/2, INTERNAL_ERROR, SSL_ERROR_SYSCALL, Curl error (56), repo.openeuler.org, MIRROR, yum install, No more mirrors to try

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
- 失败原因: openEuler 24.03-LTS-SP4 官方 yum 仓库 `repo.openeuler.org` 在 aarch64 构建节点上出现 HTTP/2 流传输错误（`INTERNAL_ERROR`）和 SSL 读取系统异常（`SSL_ERROR_SYSCALL`），导致部分 RPM 包下载失败。其中 `gcc`、`kernel-headers`、`perl-MIME-Base64` 在重试后成功下载，但 `vim-common`（`git` 的传递依赖）在所有镜像源重试后仍下载失败，导致本次 `yum install` 命令整体中止。

### 与 PR 变更的关联
PR 变更新增了一个正确的 brpc 1.16.0 Dockerfile，其 `yum install` 命令列出的软件包（`git gcc gcc-c++ make cmake which openssl-devel gflags-devel protobuf-devel protobuf-compiler abseil-cpp-devel leveldb-devel snappy-devel`）均为构建 brpc 的合理依赖，Dockerfile 语法和逻辑无错误。失败纯粹由 `repo.openeuler.org` 仓库服务器在构建时的网络传输不稳定引起，与 PR 代码逻辑无关。任何需要从该仓库下载大量 RPM 包的新 Dockerfile 提交在同一时间段均可能遭遇相同问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。该失败是 `repo.openeuler.org` 仓库服务器的暂时性网络/HTTP 层面问题，与 PR 代码无关。等待仓库服务器恢复稳定后重新触发 CI 构建即可。从日志中可见 `gcc`、`kernel-headers`、`perl-MIME-Base64` 三个包在自动重试后均成功下载，说明 yum 自带的重试机制对偶发性网络抖动有效，但 `vim-common` 持续失败表明构建时仓库侧存在持续性故障。

### 方向 2（置信度: 低）
如果频繁复现（连续多次构建均失败），可在 Dockerfile 的 `yum install` 前添加 `RUN echo "retries=10" >> /etc/yum.conf && echo "timeout=300" >> /etc/yum.conf` 以增加 yum 的重试次数和超时时间，提升对抗网络波动的容错能力。但此方向应与项目维护者确认是否符合 Dockerfile 规范，因为引入此类网络容错配置属于 workaround 而非根本解决。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段是否存在已知的服务不可用或降级事件
- 确认 aarch64 构建节点 (`ecs-build-docker-aarch64-04-sp`) 的网络连通性是否正常
- 如果该失败在多次重试后仍然复现且其他 SP4 镜像正常构建，需进一步排查是否该 Dockerfile 的 173 个 RPM 包安装量触发了 yum 连接池耗尽或仓库侧的速率限制
