# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, aarch64, yum install, No more mirrors to try

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
- 失败原因: CI aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 时，遭遇多次 HTTP/2 协议层传输错误（`Curl error (92): Stream error in the HTTP/2 framing layer` 和 `Curl error (56): SSL_ERROR_SYSCALL`），所有镜像重试均耗尽后下载失败。`vim-common` 是 `git` 包的传递依赖（非 Dockerfile 中显式声明），172/173 个包中仅该包最终失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个标准的 brpc Dockerfile（`yum install` 构建依赖 + `cmake` 编译 + `make install`），Dockerfile 语法和包名均正确。失败原因是 openEuler 官方仓库 `repo.openeuler.org` 的 aarch64 包分发在 CI 运行期间出现 HTTP/2 传输不稳定，属于 CI 基础设施/上游仓库的暂时性网络问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 这是一个上游仓库网络波动导致的 infra-error，应在 `repo.openeuler.org` 网络恢复后重新触发 CI 构建（retry）。如果该问题频繁出现，可考虑在 CI 层面为 yum 添加 `--retries` 参数或配置更稳定的镜像源。

## 需要进一步确认的点
- 在 CI 构建失败的同一时间段，`repo.openeuler.org` 的 aarch64 镜像服务是否发生了故障或网络抖动。
- `vim-common` 包（173 个包中最后一个被下载的）是否因为下载时间过长（构建已运行 ~22 分钟）导致 HTTP/2 连接更容易被中断。日志显示 gcc（30MB）和 kernel-headers（1.7MB）也遇到了同类 Curl error (92)，但重试后成功，而 vim-common（7.8MB）在同样遭遇 Curl error (92) 后重试耗尽，可能与重试次数配置或连接持续时间有关。
