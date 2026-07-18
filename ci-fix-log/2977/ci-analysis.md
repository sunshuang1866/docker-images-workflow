# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）从 `repo.openeuler.org` 下载 RPM 包时，多个包的下载过程中出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）和 SSL 读取失败（Curl error 56），最终 `vim-common` 包的镜像重试耗尽，`yum install` 失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件。Dockerfile 中 `yum install` 命令列出的包名均正确（`gcc`、`gcc-c++`、`cmake`、`openssl-devel`、`gflags-devel` 等），无语法错误。失败纯粹是由于 openEuler 官方仓库 `repo.openeuler.org` 的 aarch64 镜像在构建时段出现网络/服务端 HTTP/2 连接不稳定，导致 RPM 包下载失败。

## 修复方向

### 方向 1（置信度: 高）
重新触发 CI 构建流水线。此失败为 `infra-error`，由 `repo.openeuler.org` 官方仓库在 aarch64 架构上临时的 HTTP/2 网络不稳定引起。PR 的 Dockerfile 和元数据文件内容本身没有错误，等待仓库服务恢复后重新构建即可通过。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 aarch64 镜像服务在构建时段是否存在已知的网络故障或维护窗口。
- 若该仓库频繁出现此类 HTTP/2 流错误，可考虑在 yum 配置中禁用 HTTP/2（设置 `http2=false`）或添加 `retries=10` 等重试参数。
