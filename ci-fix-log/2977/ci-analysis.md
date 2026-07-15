# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库网络波动导致下载失败
- 新模式症状关键词: Curl error, Stream error in the HTTP/2 framing layer, MIRROR, No more mirrors to try, repo.openeuler.org, yum install

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
- 失败位置: Dockerfile:4-11（`RUN yum install -y ...` 步骤）
- 失败原因: CI 构建环境（aarch64 runner `ecs-build-docker-aarch64-04-sp`）在通过 `yum` 从 `repo.openeuler.org` 下载安装包时，遭遇多次 HTTP/2 流错误（Curl error 92）和 SSL 读取失败（Curl error 56），最终导致 `vim-common` 包下载耗尽所有镜像重试后失败。这是 CI 基础设施层面的网络波动问题，与 PR 代码变更无关。

### 与 PR 变更的关联
**与 PR 无关**。该 PR 仅新增了一个标准的 brpc Dockerfile（包含 `yum install` 构建依赖 → `git clone` 源码 → `cmake && make` 编译安装），以及对应的 README、image-info.yml、meta.yml 元数据更新。所有变更均为常规的镜像新增操作，Dockerfile 内容无语法错误或逻辑问题。构建在 `yum install` 阶段因 openEuler 官方仓库网络不稳定而失败，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。该失败为 CI 基础设施网络波动导致，与 PR 代码无关。等待 `repo.openeuler.org` 仓库网络恢复后重新触发 CI 构建即可。无需修改任何代码、Dockerfile 或元数据文件。

## 需要进一步确认的点
无。日志证据充分，失败根因明确：openEuler 官方 RPM 仓库在 aarch64 构建节点上出现间歇性 HTTP/2 流中断和 SSL 连接错误，属于外部依赖不可用导致的 infra-error。
