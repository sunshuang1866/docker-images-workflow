# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库 HTTP/2 传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, HTTP/2 stream, INTERNAL_ERROR, No more mirrors to try

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: aarch64 构建节点 `ecs-build-docker-aarch64-04-sp` 在通过 yum 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 系统包时，遭遇了多次 HTTP/2 帧传输异常（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`）和 SSL 读取错误（Curl error 56: `SSL_ERROR_SYSCALL`），其中 gcc、kernel-headers、perl-MIME-Base64 通过重试成功下载，但 `vim-common` 最终耗尽所有镜像重试次数后失败，导致整个 `yum install` 命令退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个 Dockerfile（以及配套的 README、image-info.yml、meta.yml），Dockerfile 中的 `RUN yum install -y` 命令语法和包名均正确无误。失败完全由 openEuler 官方软件源 `repo.openeuler.org` 在构建时段的 HTTP/2 传输不稳定导致，属于 CI 基础设施/外部依赖的瞬时网络故障。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 此失败为 openEuler 官方仓库 `repo.openeuler.org` 在构建时段的瞬时 HTTP/2 传输不稳定所致，与 PR 代码变更完全无关。建议在仓库服务恢复稳定后重新触发 CI 构建（Retry），无需修改任何文件。

### 方向 2（置信度: 低）
**若反复重试仍失败**，可考虑在 Dockerfile 的 `yum install` 前添加 yum 配置（如设置 `retries=10`、`timeout=300`、`minrate=1k` 或 `http_caching=packages`）以提高下载容错性，或在 `--setopt` 中切换备用镜像源。但当前证据强烈指向上游服务端临时故障，此方向仅在反复复现时值得考虑。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库在当前时段是否存在服务不稳定或维护窗口。
- 确认同一时段其他 openEuler 24.03-LTS-SP4 相关 PR 的 aarch64 构建是否也遭遇了相同的 HTTP/2 错误（若存在，则可确认是上游仓库问题而非本案特例）。
