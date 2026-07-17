# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: YUM镜像下载网络故障
- 新模式症状关键词: Curl error, Stream error in the HTTP/2 framing layer, SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install` 步骤）
- 失败原因: CI 在 aarch64 runner 上执行 `yum install` 下载 173 个 RPM 依赖包时，`repo.openeuler.org` 镜像源多次出现 HTTP/2 流错误（Curl error 92）和 SSL 连接中断（Curl error 56），多个包下载重试后最终 `vim-common` 包所有镜像源均尝试失败，yum 报错退出。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个 Dockerfile（brpc 1.16.0 on openEuler 24.03-LTS-SP4）及对应的 README 和元数据文件。Dockerfile 的 `yum install` 命令语法正确、依赖包列表与同类 brpc Dockerfile（如 `24.03-lts-sp3`）一致。失败的原因是 openEuler 官方 RPM 镜像源在构建时出现网络不稳定，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 即可。** 这是 openEuler 官方 RPM 镜像源 `repo.openeuler.org` 的临时网络故障，表现为 HTTP/2 流传输中断和 SSL 连接断开。此类问题通常通过重新触发 CI 流水线即可解决。如果持续失败，建议在 Dockerfile 的 `yum install` 前增加 `--retries` 或 `--setopt=retries=10` 等 yum 重试参数，或者联系 openEuler 基础设施团队排查镜像源健康状态。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 镜像源在构建时段是否有已知故障或维护。
- 如果多次重试 CI 仍然失败，检查是否仅为 aarch64 架构的特定包（如 `vim-common`、`gcc`、`kernel-headers`）反复出现问题，以排除镜像源同步不完整的情况。
