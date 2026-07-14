# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2网络故障
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`:4（`RUN yum install -y` 步骤）
- 失败原因: aarch64 CI runner 从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时，遭遇多次 HTTP/2 网络传输错误（Curl error 92: HTTP/2 stream INTERNAL_ERROR；Curl error 56: SSL read failure）。其中 gcc、kernel-headers、perl-MIME-Base64 三个包在重试后成功下载，但 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 在重试耗尽后最终失败，导致整个 yum 安装步骤退出。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 仅新增了一个标准的 brpc Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`），其中 `yum install` 安装的均为 openEuler 24.03-LTS-SP4 官方仓库中的标准包。构建失败纯粹由 `repo.openeuler.org` 在 aarch64 节点上的网络不稳定（HTTP/2 流异常断开、SSL 读取失败）导致。Dockerfile 本身没有语法或逻辑问题。

## 修复方向

### 方向 1（置信度: 高）
**等待镜像站恢复后重试。** 本次失败是 `repo.openeuler.org` 在 aarch64 构建节点上发生间歇性 HTTP/2 网络故障，属于 CI 基础设施问题。Code Fixer 无需对 Dockerfile 做任何修改。建议等待一段时间后重新触发 CI 构建（re-run），网络恢复后应能通过。

### 方向 2（置信度: 低）
**在 yum 命令中添加 `--retries` 参数增加重试次数**，例如 `yum install --setopt=retries=10 ...`，以应对镜像站的间歇性波动。但这属于非必要的防御性措施，且不能保证彻底解决底层网络问题。

## 需要进一步确认的点
- `repo.openeuler.org` 的 aarch64 仓库在构建时段（2026-07-09 13:45 UTC 前后）是否发生了网络抖动或维护
- 该 aarch64 runner 节点（`ecs-build-docker-aarch64-04-sp`）是否存在网络代理或 DNS 问题导致连接不稳定
- 同类 SP4 aarch64 构建近期是否有其他 PR 也遭遇相同错误（判断是节点问题还是镜像站全局问题）
