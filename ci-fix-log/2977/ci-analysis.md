# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像下载失败
- 新模式症状关键词: Curl error (92), HTTP/2 INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, Error downloading packages

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
- 失败位置: Dockerfile:4-11（`RUN yum install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方软件仓库（`repo.openeuler.org`）在 aarch64 架构构建期间出现间歇性网络故障，多个 RPM 包下载遭遇 HTTP/2 协议层 INTERNAL_ERROR 和 SSL 连接中断，最终 `vim-common` 包因所有镜像尝试失败导致 yum 安装整体退出。

### 与 PR 变更的关联
**与 PR 无关**。本次 PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关文档/元数据文件，`yum install` 安装的包列表与同族其他 SP 版本（如 24.03-lts-sp3）一致，属于标准构建依赖。失败纯粹是构建时间点 `repo.openeuler.org` 仓库的网络基础设施问题，属于 transient infra-error。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该失败为 openEuler 软件仓库 `repo.openeuler.org` 在构建时间点发生的临时性网络故障（HTTP/2 stream INTERNAL_ERROR + SSL_ERROR_SYSCALL），属于 infra-error，PR 代码无需任何修改。此类间歇性仓库问题通常在数分钟至数小时后自行恢复。只需重新触发 CI 即可。

## 需要进一步确认的点

- 是否需要将 `vim-common`（vim-enhanced 的弱依赖）从 yum 安装的隐式依赖中排除，减少未来受仓库波动影响的包数量（非必要，仅作为降低失败概率的优化方向）。
- 确认 `repo.openeuler.org` 在 aarch64 架构上是否长期存在 HTTP/2 不稳定性问题，若是，可考虑在 Dockerfile 中添加 yum retry 配置或切换至备用镜像站。
