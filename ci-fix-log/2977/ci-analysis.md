# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`yum install` 步骤）
- 失败原因: CI aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）在 `yum install` 下载 RPM 包时，与 `repo.openeuler.org` 之间的 HTTP/2 连接频繁出现流错误（Curl error 92: INTERNAL_ERROR）和 SSL 读取失败（Curl error 56: SSL_ERROR_SYSCALL），大部分包通过重试成功下载，但 `vim-common-9.0.2092-36` 在耗尽所有镜像重试后仍失败，导致整个 `yum install` 步骤退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关 metadata（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `yum install` 命令语法正确，安装的包名均为 openEuler 24.03-LTS-SP4 仓库中的有效包名（173 个包中的 172 个已成功下载，仅 `vim-common` 因网络问题失败）。根因是 `repo.openeuler.org` 镜像站在该构建时段对 aarch64 节点存在 HTTP/2 传输稳定性问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，触达 CI 重试即可。** 这是 `repo.openeuler.org` 镜像站的临时性 HTTP/2 网络波动问题。在 CI 中重新触发 aarch64 构建 job，大部分情况下网络恢复后即可通过。Code Fixer 无需处理此问题。

### 方向 2（置信度: 低）
**如果反复重试均失败**，可考虑在 Dockerfile 的 `yum install` 前增加重试/容错逻辑（如 `yum install --setopt=retries=10 ...`），或对 `repo.openeuler.org` 禁用 HTTP/2（`--http1.1`），但这属于缓解措施而非根因修复，且历史模式中无此先例。

## 需要进一步确认的点
- `repo.openeuler.org` 在 aarch64 构建时段是否存在已知的服务端 HTTP/2 问题。
- 同 PR 的 x86-64 构建 job 是否也遇到相同的网络问题（上下文仅提供了 aarch64 job 日志）。
- 该仓库其他同期 aarch64 构建 job 是否也出现类似 `Curl error (92)` / `Curl error (56)` 失败。

## 修复验证要求
（无需填写——本次失败为 infra-error，与 PR 代码无关，Code Fixer 无需修改任何文件。）
