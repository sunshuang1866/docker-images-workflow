# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, SSL_ERROR_SYSCALL, yum install, repo.openeuler.org

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
- 失败位置: Dockerfile:4（`RUN yum install -y ...`）— aarch64 架构构建节点
- 失败原因: `repo.openeuler.org` 仓库服务器在 CI 构建时段出现 HTTP/2 连接不稳定和 SSL 传输中断问题，导致 `yum` 下载多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）时反复失败，最终因 `vim-common` 包所有镜像源均已尝试失败而构建中止。

### 与 PR 变更的关联
与 PR 变更无关。PR 仅新增了一个标准的 brpc Dockerfile（yum 安装依赖 → git clone → cmake 构建），yum 安装的包列表（git、gcc、cmake、openssl-devel 等）均为 openEuler 24.03-LTS-SP4 官方仓库的标准包。失败完全由 `repo.openeuler.org` 仓库服务器的瞬态网络波动（HTTP/2 流异常终止、SSL 读取中断）引起，Dockerfile 本身无任何问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修复。** 这是 CI 基础设施的网络瞬态故障（仓库镜像 HTTP/2 连接异常），与 PR 代码变更无关。触发重试（retrigger CI build）即可。Code Fixer 无需处理。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 仓库服务是否已恢复稳定（可通过手动 wget 测试或重试 CI 来验证）。
- 如果多次重试同一 runner 节点仍持续出现同类 HTTP/2 错误，建议排查 `ecs-build-docker-aarch64-04-sp` 节点到 `repo.openeuler.org` 的网络链路质量。
