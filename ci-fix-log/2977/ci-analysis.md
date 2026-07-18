# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库下载中断
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`:4-11（`yum install` 步骤）
- 失败原因: CI 构建环境中 `repo.openeuler.org` 镜像仓库网络不稳定，在 aarch64 节点上下载 173 个 RPM 依赖包过程中，4 个包出现 HTTP/2 stream 错误（Curl error 92）和 SSL 读取失败（Curl error 56），其中 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 重试耗尽所有镜像后最终下载失败，导致 `yum install` 整体退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个正确的 Dockerfile（安装 brpc 1.16.0 所需编译依赖并编译）、更新了 `meta.yml`、`README.md` 及相关文档。失败发生在 Docker 构建的 `yum install` 阶段，原因是 openEuler 官方仓库（`repo.openeuler.org`）在 CI 运行时段临时性网络不稳定，与 Dockerfile 内容正确性、包名拼写或依赖关系无关。日志中多个包（gcc、kernel-headers、perl-MIME-Base64）都曾遇到同类网络错误但随后重试成功，说明仓库服务在其间处于间歇性不可靠状态。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，直接重试 CI。** 该失败属于 CI 基础设施层面（镜像仓库临时网络波动），与 Dockerfile 或 PR 变更无关。在 openEuler 24.03-LTS-SP4 官方仓库网络恢复正常后重新触发 CI 构建即可通过。

## 需要进一步确认的点
- `repo.openeuler.org` 在构建时段是否存在已知的服务降级或网络故障
- 该 CI runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否存在间歇性问题
- 同类使用 `openEuler:24.03-lts-sp4` 基础镜像的其他 Dockerfile 在同时段是否也出现类似网络错误
