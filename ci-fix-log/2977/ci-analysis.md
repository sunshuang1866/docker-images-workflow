# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, Stream error, yum install, No more mirrors to try

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
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建 Docker 镜像时，`yum install` 从 `repo.openeuler.org` 下载 RPM 包期间遭遇多次 HTTP/2 流错误（Curl error 92）和 SSL 连接中断（Curl error 56）。yum 在大多数 RPM 包上能通过重试成功下载，但 `vim-common` 包（第 173/173 个包）在重试后仍然失败，导致整个安装步骤退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 中 `yum install` 命令本身语法正确、包名有效（参照已有 `24.03-lts-sp3` 版本的 Dockerfile 模式），172/173 个 RPM 包已成功下载。失败原因是 `repo.openeuler.org` 镜像站在 CI 构建期间对 aarch64 runner 的 HTTP/2 连接不稳定，属于 CI 基础设施/网络问题。

## 修复方向

### 方向 1（置信度: 低）
**无需修改 Dockerfile。** 此次失败为 `repo.openeuler.org` 镜像站的临时网络波动导致。建议直接重新触发 CI 构建（retry），在网络恢复后应能正常通过。

### 方向 2（置信度: 低）
如果该镜像站对 aarch64 runner 的网络问题频繁发生，可考虑在 Dockerfile 的 `yum install` 前添加重试逻辑（如 `yum install -y --setopt=retries=10 ...` 或将 `yum install` 包裹在 `for` 循环中重试），但这属于治标不治本的方案。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI aarch64 runner 所在网络中当前是否稳定可访问
- 检查同时间段其他 PR 在 aarch64 runner 上是否有相同的 yum 下载失败现象，以排除 runner 节点自身的网络问题
