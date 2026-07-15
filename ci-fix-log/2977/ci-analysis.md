# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站网络波动
- 新模式症状关键词: Curl error, HTTP/2 framing layer, Stream error, Cannot download, repo.openeuler.org, error downloading packages

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`yum install` 步骤）
- 失败原因: CI 构建环境（aarch64 runner `ecs-build-docker-aarch64-04-sp`）在通过 `yum install` 从 `repo.openeuler.org` 下载 RPM 包时，遭遇多次 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）和 SSL 读取错误（Curl error 56），导致 `vim-common` 等包最终下载失败，"yum install" 整体退出码为 1。这是典型的 CI 基础设施网络波动问题。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个标准的 Dockerfile（yum install 依赖 → git clone → cmake → make），外加 README.md、image-info.yml、meta.yml 三个文件的元数据更新。Dockerfile 中 `yum install` 列举的包名（git, gcc, gcc-c++, make, cmake, openssl-devel, gflags-devel, protobuf-devel, abseil-cpp-devel, leveldb-devel, snappy-devel）均为 openEuler 24.03-LTS-SP4 仓库中的合法包名。失败发生在 aarch64 节点下载 RPM 的网络层面，与 Dockerfile 内容无关。日志显示部分包已下载成功（如 abseil-cpp、cmake、dbus、cpp 等），证明包名和版本不存在问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施网络故障（infra-error），应通过重试 CI job 解决。具体建议：
- 在 Jenkins 上重新触发 aarch64 构建任务。
- 若多次重试均失败，检查 `repo.openeuler.org` 的 CDN/镜像站在 aarch64 节点所在网络的连通性，必要时由运维团队排查 `ecs-build-docker-aarch64-04-sp` 节点的网络路由或 HTTP/2 代理配置。

## 需要进一步确认的点
- 确认同一时间段内其他 PR 的 aarch64 构建是否也失败——若同样失败，则证实为镜像站临时故障。
- 确认 `repo.openeuler.org` 当时是否存在服务降级或网络抖动（运维侧排查）。
