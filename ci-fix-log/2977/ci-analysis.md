# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库网络抖动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, repo.openeuler.org, No more mirrors to try, yum

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: `repo.openeuler.org` 仓库服务不稳定，频繁出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接中断（Curl error 56: SSL_ERROR_SYSCALL）。yum 对多数受影响的包（如 `gcc`、`kernel-headers`、`perl-MIME-Base64`）通过重试成功下载，但 `vim-common`（7.8 MB，由 `git` 包间接依赖引入）的重试次数耗尽，导致整个 `yum install` 步骤以 exit code 1 失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个结构正确的 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`），该 Dockerfile 使用了与其他 openEuler 24.03-LTS-SP4 镜像相同的 `yum install` 模式和依赖声明。失败发生在 Docker 构建的第一步（第 4 行）——从 `repo.openeuler.org` 下载 RPM 包阶段，这是 CI 基础设施/上游仓库的网络问题，不是 PR 代码变更（新增 Dockerfile、更新 README、更新 meta.yml）引起的。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI**。这是 `repo.openeuler.org` 仓库的临时网络问题（HTTP/2 流错误和 SSL 连接中断），非代码缺陷。在仓库服务恢复稳定后重新触发 CI 构建即可通过。`vim-common` 包（7.8 MB）体积较大，受网络抖动影响概率更高，但这是偶发事件。

### 方向 2（置信度: 低）
若 CI 反复因同一网络问题失败，可考虑在 Dockerfile 的 `yum install` 命令中添加 `--retries 10 --retry-delay 30` 参数（需确认 openEuler 24.03-LTS-SP4 的 yum/dnf 版本支持），提高对临时网络波动的容忍度。但这只是缓解措施，不解决根因。

## 需要进一步确认的点
- `repo.openeuler.org` 在 CI 构建时段（2026-07-09 13:45 UTC 附近）是否存在已知的 CDN/服务端问题
- 该 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络路径是否存在稳定性问题
- 同一时段其他 PR 的 aarch64 CI 构建是否也出现了类似的 `repo.openeuler.org` 下载失败（如果是广泛问题则确认是仓库侧故障）
