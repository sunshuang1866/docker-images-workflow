# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像下载网络故障
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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

- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install ...` 步骤）
- 失败原因: CI 构建环境（aarch64 runner `ecs-build-docker-aarch64-04-sp`）在执行 `yum install` 从 `repo.openeuler.org` 下载 aarch64 RPM 包时，遭遇连续的 HTTP/2 协议层错误（`Curl error 92: INTERNAL_ERROR`）和 SSL 连接中断（`Curl error 56: SSL_ERROR_SYSCALL`），最终 `vim-common` 包耗尽所有镜像重试后下载失败，导致整个 yum 安装事务中止。

### 与 PR 变更的关联

**与 PR 变更无关。** 本次 PR 新增的 Dockerfile 语法正确、依赖包列表完整有效。失败纯粹是 openEuler 官方软件仓库 `repo.openeuler.org` 在构建时段对 aarch64 runner 存在网络服务不稳定问题（HTTP/2 stream 被服务端异常关闭、SSL 连接被对端重置）。PR 的 Dockerfile 没有引入任何错误。

## 修复方向

### 方向 1（置信度: 高）
此失败为 CI 基础设施问题（`infra-error`），与 PR 代码无关。**无需修改 Dockerfile 或任何 PR 文件。** 建议触发 CI 重试（re-run），在网络状况正常时构建即可通过。如果多次重试仍失败，需排查 `repo.openeuler.org` 对特定 aarch64 runner 节点的网络可达性。

### 方向 2（可选，置信度: 低）
若 `repo.openeuler.org` 持续不稳定，可考虑在 `RUN` 命令开头添加 `--retries` 或分步重试逻辑（如 `yum install --setopt=retries=10 ...`），但这并非根本解决方案，不推荐。

## 需要进一步确认的点

- `repo.openeuler.org` 在构建时段是否存在已知的服务中断或降级。
- 其他同时段运行的 aarch64 构建 job 是否也出现相同类型的 Curl/HTTP/2 错误（可确认是否为仓库侧问题而非 runner 个别网络问题）。
- 该 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）与 `repo.openeuler.org` 之间的网络链路是否存在间歇性故障。
