# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2传输中断
- 新模式症状关键词: Curl error 92, Stream error in the HTTP/2 framing layer, repo.openeuler.org, yum download, INTERNAL_ERROR, SSL_ERROR_SYSCALL

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤中的 `RUN` 指令）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，从 `repo.openeuler.org` 下载 173 个 RPM 包的过程中，多个包（gcc、kernel-headers、perl-MIME-Base64、vim-common）遭遇 HTTP/2 流传输错误（curl error 92: INTERNAL_ERROR）和 SSL 连接中断（curl error 56: SSL_ERROR_SYSCALL）。前三次 yum 通过镜像重试机制恢复，但 `vim-common` 重试后所有镜像均已耗尽，yum 安装失败，导致整个 `RUN` 步骤退出码为 1，Docker 构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了 brpc 的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中的 `yum install` 命令写法与仓库内其他同类 Dockerfile 完全一致。失败源于 `repo.openeuler.org` 软件源在接受 aarch64 架构的大文件 RPM 下载时 HTTP/2 连接层不稳定，属于 CI 基础设施问题，非代码缺陷。

## 修复方向

### 方向 1（置信度: 中）
**重试 CI 构建。** 此类 HTTP/2 流错误（curl error 92）和 SSL 连接中断（curl error 56）通常是远程服务器端或中间网络设备的临时性故障。在 openEuler 软件源恢复正常后重新触发 CI 即可通过。无需修改 Dockerfile 或任何代码。

### 方向 2（置信度: 低）
若重试后仍然失败，可考虑在 `yum install` 前添加 yum 配置调整，例如启用 HTTP/1.1 回退（`--setopt=curl.no_http2=true`）以规避 HTTP/2 流错误，或添加 `--retries` 参数增加重试次数。但此类方案属于绕过而非修复根因，不推荐优先采用。

## 需要进一步确认的点
1. 确认 `repo.openeuler.org` 在 aarch64 架构下对 openEuler 24.03-LTS-SP4 软件源的服务状态是否正常（检查是否有 CDN 节点异常或 SSL 证书问题）。
2. 检查 CI 构建节点 `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络连通性和 MTU 设置——HTTP/2 INTERNAL_ERROR 有时由网络路径 MTU 不匹配触发。
3. 该 PR 同时新增了一个全新 Dockerfile（24.03-lts-sp4 镜像版本），该基础镜像的 aarch64 RPM 源在首次构建时需下载 173 个包（总计 148 MB），比已有 sp3 镜像的下载量大得多，增加了网络中断概率。可确认 sp3 版本的同类构建在近期是否也遇到类似波动。
