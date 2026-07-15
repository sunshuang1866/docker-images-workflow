# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org, aarch64

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
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时，多个包遭遇 HTTP/2 流中断（Curl error 92）和 SSL 连接重置（Curl error 56）。gcc、kernel-headers、perl-MIME-Base64 通过镜像重试成功下载，但 `vim-common` 在重试所有镜像后仍失败，导致 yum 事务回滚、构建失败。

### 与 PR 变更的关联
**与 PR 改动无关**。PR 仅新增了一个符合规范的 Dockerfile（与已有 SP3 版本结构一致）及配套元数据文件（README.md、image-info.yml、meta.yml）。构建失败发生在 `yum install` 阶段——该步骤是 Dockerfile 中第一个实质操作（在基础镜像上安装编译依赖），错误完全是 `repo.openeuler.org` 仓库服务器端的网络传输问题，不涉及 PR 代码的任何逻辑错误或包名拼写错误。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。这是典型的 CI infra-error，由 openEuler 官方 RPM 仓库（`repo.openeuler.org`）的网络波动导致 aarch64 包下载中断。历史上 gcc、kernel-headers 等包均通过 yum 内置的镜像重试机制自动恢复，本次仅 vim-common 运气不佳耗尽了所有镜像尝试。等待仓库网络恢复后重新触发 CI 构建即可通过，无需修改任何代码。

### 方向 2（置信度: 低）
若重试多次仍持续失败，可能是 openEuler 24.03-LTS-SP4 的 aarch64 仓库中某些 RPM 包确实存在 HTTP/2 服务端配置问题。可向 openEuler 基础设施团队反馈 `repo.openeuler.org` 的 HTTP/2 流稳定性问题。

## 需要进一步确认的点
- 该失败是否仅在 aarch64 runner 上出现、x86-64 runner 是否正常（日志仅包含 aarch64 构建过程，需确认 x86-64 侧的构建结果）
- 重试 CI 构建后是否仍复现相同错误（若持续复现，则可能是仓库侧问题而非临时波动）

## 修复验证要求
无需验证（infra-error，无代码修改）。
