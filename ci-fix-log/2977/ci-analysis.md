# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输错误
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 framing layer, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org, aarch64

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y` 步骤）
- 失败原因: CI 构建节点（`ecs-build-docker-aarch64-04-sp`，aarch64 架构）在执行 `yum install` 从 `repo.openeuler.org` 下载 173 个 RPM 包的过程中，多个包遭遇 HTTP/2 传输层错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接中断（Curl error 56: SSL_ERROR_SYSCALL）。虽然有部分包在重试后成功下载，但 `vim-common` 包最终耗尽所有镜像重试次数而彻底失败，导致整个 `yum install` 步骤以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 改动无关。** 本次 PR 的变更内容仅为：
1. 新增 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`（brpc 1.16.0 镜像构建文件）
2. 更新 `README.md` 和 `image-info.yml`（添加镜像说明文档条目）
3. 更新 `meta.yml`（注册新版本路径）

Dockerfile 本身的 `yum install` 命令语法正确，安装的包（git、gcc、gcc-c++、make、cmake、openssl-devel、gflags-devel、protobuf-devel、protobuf-compiler、abseil-cpp-devel、leveldb-devel、snappy-devel）均为 openEuler 24.03-LTS-SP4 仓库中的有效包名。失败完全由 `repo.openeuler.org` 镜像站在当前时间点的网络不稳定（HTTP/2 流异常中断、SSL 连接复位）导致，与 Dockerfile 内容或 PR 的任何代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是典型的 CI 基础设施网络波动导致的失败，yum 仓库 `repo.openeuler.org` 在 aarch64 架构上的 HTTP/2 服务临时不稳定。Dockerfile 无需修改，等待仓库镜像站恢复后重试构建即可。如果该问题持续复现，可考虑在 Dockerfile 的 `yum install` 前添加 `yum makecache` 或增加重试参数来提升容错性，但这属于优化而非必要修复。

## 需要进一步确认的点
- `repo.openeuler.org` 的 aarch64 镜像站在报告时段的服务状态（是否为临时性中断或区域性网络问题）
- 如果重试后仍然持续失败，需要确认是否是 openEuler 24.03-LTS-SP4 aarch64 仓库中 `vim-common-9.0.2092-36.oe2403sp4` 包本身在镜像站存在问题（如包文件损坏）
