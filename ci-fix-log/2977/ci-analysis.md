# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库网络抖动
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), Failure when receiving data from the peer, repo.openeuler.org, No more mirrors to try

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（yum install 步骤）
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在 yum 安装依赖包时，从 `repo.openeuler.org` 下载 RPM 包的过程中遭遇多次间歇性网络故障（HTTP/2 流错误 `Curl error 92` 和 SSL 连接中断 `Curl error 56`）。gcc、kernel-headers、perl-MIME-Base64 三个包先后触发 `[MIRROR]` 重试警告后恢复，但 `vim-common` 包的下载在重试后仍失败，yum 退出码为 1。基础镜像拉取和 172/173 个包下载均正常完成，说明网络并非完全不通，而是存在间歇性波动。

### 与 PR 变更的关联
与 PR 变更**完全无关**。PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 内容本身无任何语法或逻辑错误，`yum install` 指定的包名（gcc、cmake、openssl-devel 等）均为 openEuler 仓库中的合法包名。失败原因是 openEuler 官方软件源与 CI aarch64 runner 之间的网络链路出现了临时性故障。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建流水线。** 此类 `repo.openeuler.org` 的 HTTP/2 流错误和 SSL 连接中断通常是暂时性的网络波动（服务端负载波动或链路瞬断）。从日志看，前三组报错的包（gcc、kernel-headers、perl-MIME-Base64）在重试后均成功下载，最后一组 vim-common 的重试次数耗尽才导致整体失败——通过网络状况好转或扩大重试次数即可解决。建议直接重新触发 CI 构建。

### 方向 2（置信度: 中）
**在 Dockerfile 中为 yum 增加重试参数**以提高对间歇性网络故障的容忍度。若网络问题持续出现，可在 `yum install` 命令中添加 `--retries 5 --retry-delay 30` 等参数，使 yum 对下载失败的包进行更多次重试，避免因单次网络抖动导致整次构建失败。

## 需要进一步确认的点
- 确认 x86_64 架构的同一分支构建是否也失败（当前日志仅包含 aarch64 runner 的构建输出）
- 确认 `repo.openeuler.org` 在该时间段是否存在服务端故障或负载过高的情况
- 若重试后仍失败，需排查 CI runner `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络链路是否存在持续性丢包或 DNS 解析问题

## 修复验证要求
（无需验证——失败类型为 infra-error，不存在需要修改的正则或代码）
