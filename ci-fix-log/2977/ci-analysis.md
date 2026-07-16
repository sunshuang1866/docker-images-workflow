# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源HTTP/2下载中断
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, repo.openeuler.org, yum install, No more mirrors to try

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ...
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for ... [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ...
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: CI aarch64 构建节点的 Docker build 过程中，`yum install` 从 `repo.openeuler.org` 下载 RPM 包时遭遇间歇性 HTTP/2 流中断（Curl error 92: INTERNAL_ERROR）和 SSL 连接断开（Curl error 56: SSL_ERROR_SYSCALL）。前三个失败的包（gcc、kernel-headers、perl-MIME-Base64）经重试后成功下载，但 `vim-common` 耗尽所有镜像重试次数后永久失败，导致整个 RUN 步骤退出码 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、README 和元数据文件，Dockerfile 中 `yum install` 的包列表语法正确、包名有效。失败完全由 `repo.openeuler.org` 软件源在 CI 执行期间的网络波动（HTTP/2 流错误）引起，属于基础设施层面的临时间歇性问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复——CI 基础设施重试即可。** 此失败为 `repo.openeuler.org` 软件源在 CI 执行时刻的临时间歇性网络问题。同类错误在本次构建中已多次出现（gcc、kernel-headers、perl-MIME-Base64），其中大部分通过 yum 的内置重试机制成功恢复，仅 `vim-common` 因重试次数耗尽而失败。建议在 openEuler 24.03-LTS-SP4 软件源网络状况良好时重新触发 CI 构建（re-run），通常即可通过。

## 需要进一步确认的点
- 确认 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 是否在软件源中实际存在且可被外部正常下载（验证非 404 类永久不可用问题）。从日志看，yum 已成功解析包列表并下载了 172/173 个包，说明仓库索引和绝大多数包均可用，仅下载传输阶段失败，因此包存在的可能性极高。
- 若多次重试仍然失败，需排查 CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络路由是否稳定，或考虑为该仓库源配置 HTTP/1.1 降级以规避 HTTP/2 流中断。

## 修复验证要求
无需代码修复，Code Fixer 无需处理。若后续 CI 反复出现同类问题，再行排查网络层。
