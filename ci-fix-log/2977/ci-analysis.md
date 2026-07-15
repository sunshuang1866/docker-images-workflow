# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络波动
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
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI aarch64 构建节点在通过 yum 从 `repo.openeuler.org` 下载 RPM 包时，`repo.openeuler.org` 多次出现 HTTP/2 流传输错误（Curl error 92: HTTP/2 stream INTERNAL_ERROR）和 SSL 连接中断（Curl error 56: SSL_ERROR_SYSCALL），173 个依赖包中的 `vim-common` 因镜像重试次数耗尽而最终下载失败，导致整个 `yum install` 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个 Dockerfile、更新了 README.md、image-info.yml 和 meta.yml，所有变更均为正确的配置/文档类修改。Dockerfile 中 `yum install` 的包名列表正确，172/173 个包均已成功下载安装，仅 `vim-common` 因 openEuler 官方仓库的网络瞬时故障而下载失败。日志中多个包（gcc、kernel-headers、perl-MIME-Base64）也遇到了同样的 HTTP/2 流错误和 SSL 错误，但通过 yum 内置重试机制最终成功下载，说明 `repo.openeuler.org` 在该构建时段存在间歇性网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重新触发 CI 构建即可。** 这是 openEuler 官方仓库 `repo.openeuler.org` 的临时网络波动（HTTP/2 流中断 + SSL 连接异常），与 PR 中的 Dockerfile、README.md、image-info.yml、meta.yml 均无关。在仓库服务恢复正常后重跑 CI，yum install 步骤应能顺利完成。

### 方向 2（置信度: 中）
若该问题持续出现（说明 `repo.openeuler.org` 与 aarch64 构建节点之间存在持续性的网络连通性问题），可考虑在 `yum install` 命令前添加重试逻辑，例如 `yum install -y ... || yum install -y ...`，或配置 yum 的 `retries` 和 `timeout` 参数以增强网络容错能力。但这属于 CI 基础设施层面的优化，不属于本次 PR 的修复范围。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段（2026-07-09 13:44 UTC 左右）是否存在已知的服务中断或网络波动。
- 如果重试后仍然失败，需确认 aarch64 构建节点到 `repo.openeuler.org` 的网络路由是否稳定，是否存在防火墙/代理配置导致的 HTTP/2 连接异常断开问题。
