# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, repo.openeuler.org, yum install, RPM download, No more mirrors to try

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（yum install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库（`repo.openeuler.org`）在 aarch64 架构构建期间出现 HTTP/2 传输层错误（Curl error 92）和 SSL 连接中断（Curl error 56），导致多个 RPM 包下载失败。其中 `vim-common` 包在重试所有镜像源后仍无法下载，yum 安装整体失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 这是一个纯粹的 CI 基础设施问题。PR 新增的 Dockerfile 在语法和依赖声明上均无错误——`yum install` 步骤列出的所有包名（git、gcc、gcc-c++、cmake、openssl-devel、gflags-devel、protobuf-devel 等）均为 openEuler 24.03-LTS-SP4 仓库中合法存在的软件包。日志中 `Dependencies resolved` 阶段（#7 198.5）也确认了这一点：173 个包均被正确解析，下载才刚启动就遭遇仓库服务端的 HTTP/2 传输异常。

尤其需要注意的是，`vim-common` 是一个**传递依赖**（由 git 工具链间接引入），并非 Dockerfile 显式声明的包。前三个包（gcc、kernel-headers、perl-MIME-Base64）虽也遇到 Curl 错误，但 yum 的重试机制最终成功下载，仅 `vim-common` 耗尽所有镜像后彻底失败。这说明问题本质是仓库服务端的**间歇性 HTTP/2 连接不稳定**，而非 PR 代码引入了不存在的依赖。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码。** 在 CI 环境中重新触发构建（retry）。由于 HTTP/2 传输错误是间歇性的，后续构建有较大概率成功。如果多次重试均失败，应考虑：
- 检查 `repo.openeuler.org` 的 aarch64 仓库镜像服务状态（是否正在维护或存在负载问题）
- 联系 openEuler 基础设施团队排查仓库服务器的 HTTP/2 配置

### 方向 2（置信度: 低）
如果问题持续且无法等待仓库恢复，可考虑在 Dockerfile 的 `yum install` 命令前添加 `yum-config-manager` 配置，将最大重试次数或超时时间调高，或临时切换为仅使用 HTTP/1.1 协议下载。但这属于规避方案，不解决根本问题，且会增加构建时间。

## 需要进一步确认的点
- `repo.openeuler.org` 在 CI 构建时段（2026-07-09 13:44-14:08 UTC）是否存在已知的 aarch64 仓库服务中断
- x86_64 架构的同 PR 构建是否成功（日志中仅包含 aarch64 runner 的输出，无法确认另一架构的结果）

## 修复验证要求
不适用（infra-error，无需修改代码）。
