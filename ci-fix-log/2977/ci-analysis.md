# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源下载网络故障
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `yum install` 时，从 `repo.openeuler.org` 下载 173 个 RPM 包期间发生多次网络传输错误（4 个包受影响：gcc、kernel-headers、perl-MIME-Base64、vim-common），其中 3 个在重试后成功，但 `vim-common`（7.8MB）耗尽所有镜像源后下载失败，导致整个 `yum install` 步骤以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile（25 行）及对应的 README、image-info.yml、meta.yml 更新。Dockerfile 中的 `yum install` 命令语法正确，所需包名均为 openEuler 24.03-LTS-SP4 仓库中已有的有效包（yum 已成功解析出全部 173 个包的依赖关系并开始下载）。失败完全由 `repo.openeuler.org` 仓库源在 aarch64 架构上的网络传输不稳定（HTTP/2 流异常断开、SSL 读取失败）导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施的临时性网络问题（`repo.openeuler.org` 的 HTTP/2 服务对 aarch64 大量并发包下载存在流不稳定）。应重新触发 CI 构建（retry），在网络恢复后构建应可自行成功。

### 方向 2（置信度: 中）
若重试后仍频繁出现同类问题，可考虑在 Dockerfile 的 `yum install` 命令中添加重试参数（如 `yum install --retries=5 --setopt=retries=5 ...`），但鉴于这是上游仓库源的瞬时网络故障而非 Dockerfile 配置问题，该方案并非根本解决之道。若问题持续，应联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 aarch64 仓库源 CDN / mirror 健康状态。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 aarch64 架构上的 CDN / mirror 服务是否存在已知的间歇性不稳定问题。
- 确认 24.03-LTS-SP4 的 aarch64 RPM 仓库是否在某些时间段有维护或负载过高的情况。
- 若重试多次均失败，需检查 CI 构建节点 `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络连通性和 MTU/HTTP2 配置兼容性。
