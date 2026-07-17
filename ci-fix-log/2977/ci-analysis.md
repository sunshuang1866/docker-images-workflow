# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 framing layer, repo.openeuler.org, yum install, aarch64

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`yum install` 步骤）
- 失败原因: 在 aarch64 runner 上执行 `yum install` 时，从 `repo.openeuler.org` 下载多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）遭遇 HTTP/2 流错误（Curl error 92）和 SSL 读取失败（Curl error 56），其中 `vim-common` 包在耗尽所有镜像源重试后仍下载失败，导致整个 yum 事务中断。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `yum install` 命令格式正确，所列包名均为 openEuler 24.03-LTS-SP4 仓库中的合法包名。失败根因是 CI 构建节点（`ecs-build-docker-aarch64-04-sp`）与 `repo.openeuler.org` 之间的网络连接不稳定，导致 HTTP/2 流异常中断。

## 修复方向

### 方向 1（置信度: 高）
此为 **CI 基础设施网络问题**（infra-error），PR 代码无需修改。建议重新触发 CI 构建（retry），在网络状况良好的时间段重试通常可以成功。若多次重试仍失败，需排查以下两点：
1. 确认 `repo.openeuler.org` 的 CDN/镜像源在 aarch64 节点的可达性和稳定性。
2. 检查 CI runner `ecs-build-docker-aarch64-04-sp` 的网络环境（代理配置、DNS 解析、防火墙规则）。

## 需要进一步确认的点
- `repo.openeuler.org` 在故障时段是否存在已知的 CDN 节点故障或 HTTP/2 服务端问题。
- 同一时段其他 openEuler 24.03-LTS-SP4 镜像（如 x86_64 架构）的构建是否也出现类似下载错误，以排除 repo 侧全局性问题。
- CI runner 网络策略是否对 HTTP/2 长连接有限制（部分代理/防火墙会阻断 HTTP/2 stream）。
