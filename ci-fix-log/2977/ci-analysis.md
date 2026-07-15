# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: yum 仓库下载失败
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, aarch64

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
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `yum install` 时，从 `repo.openeuler.org` 下载 aarch64 架构 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）连续遭遇 HTTP/2 传输层错误（`INTERNAL_ERROR`、`SSL_ERROR_SYSCALL`），其中 `vim-common` 耗尽了所有重试镜像后安装失败，导致整个 `yum install` 命令退出码为 1。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 新增的 Dockerfile 内容本身正确——`yum install` 依赖包列表语法无误，基础镜像 `openeuler/openeuler:24.03-lts-sp4` 拉取成功（`#6 DONE 10.1s`），包依赖解析也正常（173 个包, Transaction Summary 正常）。失败纯粹是因为 `repo.openeuler.org` 仓库对 aarch64 架构包在构建时段（2026-07-09 13:44-14:06 UTC）存在 HTTP/2 传输稳定性问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施网络问题——`repo.openeuler.org` 仓库在构建时段对 aarch64 包的 HTTP/2 传输不稳定。直接重新触发 CI 构建（rerun），待仓库服务恢复后构建大概率会通过。已有多个包（gcc、kernel-headers）在重试后成功下载，仅 vim-common 在耗尽所有重试后仍失败，说明问题是间歇性的而非持续不可达。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段（2026-07-09 UTC 13:44-14:06）是否存在已知的服务降级或网络故障。
- 确认该镜像的其他架构（x86-64/amd64）构建是否也遇到同样问题，以判断是仓库整体故障还是仅 aarch64 仓库分区异常。
