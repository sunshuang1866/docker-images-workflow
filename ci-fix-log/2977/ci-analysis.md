# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Repo镜像HTTP2错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, OpenSSL SSL_read, SSL_ERROR_SYSCALL, yum install

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: CI aarch64 Runner（`ecs-build-docker-aarch64-04-sp`）在 `yum install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包的 HTTP/2 连接遭遇 `Stream error (INTERNAL_ERROR)` 和 `SSL_ERROR_SYSCALL` 网络层错误。前三个包（gcc、kernel-headers、perl-MIME-Base64）在重试后成功下载，但 `vim-common` 耗尽所有重试次数后最终失败，导致整个 `yum install` 命令退出码 1。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 仅为新增 brpc 1.16.0 on openEuler 24.03-LTS-SP4 的 Dockerfile 及相关元数据文件。Dockerfile 中的 `yum install` 命令本身语法正确，安装的均为 openEuler 24.03-LTS-SP4 仓库中存在的标准软件包。失败是 openEuler 官方软件源 `repo.openeuler.org` 的 CDN/镜像节点在构建时段发生 HTTP/2 连接不稳定的基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施的临时性网络故障（openEuler 软件源 HTTP/2 连接不稳定），**非代码问题，无需修改 PR 代码**。建议直接触发 CI 重跑（retry），大概率可以成功。若反复失败，可考虑在 Dockerfile 的 `yum install` 前添加 `yum makecache` 或设置 yum 的 `retries` 参数增加重试次数以提升容错性。

## 需要进一步确认的点
- openEuler 软件源 `repo.openeuler.org` 在构建时段（2026-07-09 13:44 UTC 前后）是否存在已知的网络中断或 CDN 故障公告
- 同一时段其他使用 openEuler 24.03-LTS-SP4 基础镜像的 PR 是否也遇到相同的 yum 下载失败
- `ecs-build-docker-aarch64-04-sp` Runner 节点的网络出口是否存在对 `repo.openeuler.org` 的连接限制或防火墙策略变更
