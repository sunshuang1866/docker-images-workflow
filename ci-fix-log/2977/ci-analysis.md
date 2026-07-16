# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, INTERNAL_ERROR, repo.openeuler.org, No more mirrors to try

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install -y ...` 步骤）
- 失败原因: 在 aarch64 runner 上执行 `yum install` 时，`repo.openeuler.org` 仓库服务器多次出现 HTTP/2 流内部错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接中断（Curl error 56: SSL_ERROR_SYSCALL）。DNF 对 gcc、kernel-headers、perl-MIME-Base64 等包的重试成功，但 `vim-common` 包耗尽了所有镜像重试次数，最终导致整个安装步骤失败。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了 brpc 的 Dockerfile（含标准 `yum install` 依赖列表）、更新了 README.md、image-info.yml 和 meta.yml。Dockerfile 中 `yum install` 命令的语法和包名均正确。失败完全由 `repo.openeuler.org` 仓库服务器的 HTTP/2 流传输问题导致，属于 CI 基础设施/外部依赖问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。该失败是网络层面的临时性问题（openEuler 仓库服务器 HTTP/2 流不稳定），与代码变更无关。建议在非高峰时段触发 CI 重新构建，或等待仓库服务恢复后重试。

### 方向 2（置信度: 低）
若重试多次仍持续失败，可考虑在 Dockerfile 中的 `yum install` 之前添加重试机制（如在 `yum install` 失败时自动 retry），或为 `yum` 配置 `retries` 和 `timeout` 参数以增强网络容错。但这属于对基础设施问题的防御性 workaround，非根因修复。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 服务器在构建时段是否存在已知的 HTTP/2 服务异常或维护公告。
- 确认 x86_64 架构的对应构建 job 是否同样失败（若 x86_64 通过，则确认问题仅影响 aarch64 仓库节点）。
- 确认 CI 调度器是否支持对该类 `infra-error` 自动重试（如果可以，无需修改 Dockerfile）。
