# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Yum仓库HTTP/2网络故障
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, No more mirrors to try, Error downloading packages

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 构建节点（`ecs-build-docker-aarch64-04-sp`）在通过 yum 从 `repo.openeuler.org` 下载 aarch64 RPM 包时，遭遇多次 HTTP/2 协议层流错误（Curl error 92: `Stream error in the HTTP/2 framing layer`）和 SSL 连接中断（Curl error 56），最终包 `vim-common-9.0.2092-36` 下载失败，yum 耗尽所有镜像重试后报错退出。

### 与 PR 变更的关联
**与 PR 变更无关**。此次 PR 仅新增了一个标准 Dockerfile（安装依赖 → clone 源码 → cmake 构建）以及配套的 README、image-info.yml、meta.yml 条目。构建在最早的 `yum install` 阶段即因网络问题中断，未到达 PR 特有的 cmake 构建/编译步骤。Dockerfile 中 `yum install` 的包列表（gcc, gcc-c++, cmake, openssl-devel 等）均为 openEuler 24.03-LTS-SP4 仓库的常规包，列表本身没有问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。这是典型的临时性网络故障（`repo.openeuler.org` 镜像站的 HTTP/2 连接在构建期间不稳定），与代码无关。Code Fixer 无需对代码做任何修改。等待镜像站网络恢复后重新触发 CI 构建即可。

### 方向 2（置信度: 中）
若多次重试仍然失败，可考虑在 Dockerfile 的 `yum install` 命令中添加重试参数（如 `--setopt=retries=10`），或使用 `dnf` 替代 `yum`（openEuler 24.03 中 dnf 为默认包管理器，对 HTTP/2 错误的重试策略可能不同）。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 CI 构建时段是否存在已知的服务端问题或 CDN 故障。
- 若同批次其他镜像（如 brpc 1.16.0-oe2403sp3）的 aarch64 构建也失败，则可确认为镜像站问题而非单个构建的偶发波动。

## 修复验证要求
无需验证，本次失败为 infra-error，不涉及代码修复。
