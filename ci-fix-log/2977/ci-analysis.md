# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, MIRROR, repo.openeuler.org, vim-common

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: aarch64 构建节点在下载 `openEuler 24.03-LTS-SP4` 官方镜像源（`repo.openeuler.org`）的 173 个 RPM 包时，遭遇多次 HTTP/2 协议流错误（Curl error 92: HTTP/2 stream INTERNAL_ERROR）和 SSL 读取失败（Curl error 56: SSL_ERROR_SYSCALL）。gcc、kernel-headers、perl-MIME-Base64 三个包在重试后下载成功，但第 173/173 个包 `vim-common-9.0.2092-36` 重试后仍失败，yum 耗尽所有镜像后终止安装。该错误与 PR 代码变更无关，属于 `repo.openeuler.org` 镜像站对 aarch64 架构的 HTTP/2 服务临时不稳定。

### 与 PR 变更的关联
**无关**。PR 仅新增了一个 Dockerfile（`RUN yum install` 语法正确、包名有效）和更新了 3 个元数据文件（README.md、image-info.yml、meta.yml）。构建在 `yum install` 阶段因 `repo.openeuler.org` 镜像站的网络故障而失败，172/173 个包均已成功下载，仅最后一个包因 HTTP/2 流错误导致下载失败——这是外部依赖服务端的瞬时问题，不是 PR 代码问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复，重新触发 CI 构建即可。** 该失败是 `repo.openeuler.org` 镜像站在该时间片段对 aarch64 架构的 HTTP/2 服务出现瞬时异常，导致 `vim-common` 等少数 RPM 包下载失败。日志中 gcc、kernel-headers 等包在首次 HTTP/2 流错误后也通过 yum 内置重试机制成功下载，说明问题具有自愈特征。等待镜像站恢复后重新运行 CI pipeline 即可通过。

### 方向 2（置信度: 低）
若重试后仍反复出现同样的 `Curl error (92)` 或 `Curl error (56)` 错误，可能是构建节点到 `repo.openeuler.org` 的网络路径存在问题（如中间代理/防火墙干扰 HTTP/2 多路复用）。此时应由 CI 基础设施团队排查 aarch64 构建节点的网络连通性，而非修改 Dockerfile。

## 需要进一步确认的点
- 当前 aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络稳定性和 HTTP/2 协议兼容性
- 该镜像站在同一时间片段是否对其他架构（x86_64）的下载也出现类似 HTTP/2 流错误
- 若反复出现，是否需要为 yum 添加 `--retries` 或降级使用 HTTP/1.1 的镜像源配置
