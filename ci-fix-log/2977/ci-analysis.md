# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源下载不稳定
- 新模式症状关键词: Curl error, HTTP/2 framing layer, SSL_ERROR_SYSCALL, No more mirrors to try, Error downloading packages, repo.openeuler.org

## 根因分析

### 直接错误

```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 详细错误链

在 yum 安装 173 个依赖包的过程中，`repo.openeuler.org` 的多个 RPM 包下载遭遇网络层错误：

1. **gcc** (556.2s): `Curl error (92): Stream error in the HTTP/2 framing layer ... INTERNAL_ERROR (err 2)` — 虽然最终重试成功（831.9s 处下载完成）
2. **kernel-headers** (836.2s): `Curl error (92): Stream error in the HTTP/2 framing layer ... INTERNAL_ERROR (err 2)` — 同样重试成功（855.7s 处下载完成）
3. **perl-MIME-Base64** (1029.3s): `Curl error (56): Failure when receiving data from the peer ... SSL_ERROR_SYSCALL, errno 0` — 重试成功
4. **vim-common** (1310.2s): `Curl error (92): Stream error in the HTTP/2 framing layer ... INTERNAL_ERROR (err 2)` — 所有镜像源均重试失败，触发致命错误

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install` 步骤）
- 失败原因: `repo.openeuler.org` 在 aarch64 架构 CI runner 上持续出现 HTTP/2 流中断（`INTERNAL_ERROR`）和 SSL 连接重置（`SSL_ERROR_SYSCALL`），多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载受影响，其中 vim-common 在所有镜像源重试后仍无法下载，导致 yum 安装失败。

### 与 PR 变更的关联

**此失败与 PR 变更无关。** PR 仅新增了一个 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）及配套的文档/元数据文件。Dockerfile 中的 `yum install` 命令语法正确，所选包名均为 openEuler 24.03-LTS-SP4 仓库中的有效包名。失败纯粹由 openEuler 官方软件源 `repo.openeuler.org` 在构建时段内的网络不稳定导致，属于 CI 基础设施层面的问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 这是典型的网络波动导致的一次性失败，与代码无关。在 `repo.openeuler.org` 服务恢复稳定后重新触发 CI 构建即可通过。若反复重试仍失败，可能需要 CI 运维团队排查 `repo.openeuler.org` 的 CDN/镜像节点健康状况或 CI runner 到该仓库的网络链路。

## 需要进一步确认的点

- 确认 `repo.openeuler.org` 在构建时段（2026-07-09 13:44 UTC 附近）是否存在已知的服务降级或网络故障。
- 确认 CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否稳定（可通过在该 runner 上对仓库 URL 做简单的 `curl` 连通性测试验证）。
- 若该 runner 持续出现 HTTP/2 流错误，可考虑在 yum 配置中降级为 HTTP/1.1 作为临时缓解措施。

## 修复验证要求

无需验证（无代码修复方案）。
