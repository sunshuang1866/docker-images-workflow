# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输异常
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, OpenSSL SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, aarch64

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
- 失败原因: CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在 Docker 构建过程中执行 `yum install` 时，从 `repo.openeuler.org` 的 24.03-LTS-SP4 aarch64 仓库下载 173 个 RPM 包时遭遇多次 HTTP/2 协议层传输错误（curl error 92: INTERNAL_ERROR、curl error 56: SSL_ERROR_SYSCALL），多个包（gcc、kernel-headers、perl-MIME-Base64、vim-common）在重试后仍下载失败，最终 `vim-common` 耗尽所有镜像源后彻底失败，导致 Docker 构建中断。

### 与 PR 变更的关联
与 PR 变更**无直接关联**。PR 仅新增了一个合法的 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`），其 `yum install` 命令语法正确，所请求的包名也在 24.03-LTS-SP4 仓库中真实存在（yum 已成功解析依赖树，列出了 173 个待安装包）。失败纯粹是由于 `repo.openeuler.org` 的 aarch64 仓库在构建时间段内 HTTP/2 传输不稳定，属于 CI 基础设施/上游仓库的网络可靠性问题。

## 修复方向

### 方向 1（置信度: 中）
等待上游仓库网络恢复后重试 CI。该失败为 `repo.openeuler.org` 24.03-LTS-SP4 aarch64 仓库的 HTTP/2 传输不稳定所致，属于临时性基础设施问题。可触发 CI 重新运行（re-run/retry），在仓库网络正常时段重试构建。

### 方向 2（置信度: 低）
若反复重试仍失败，可在 Dockerfile 的 `yum install` 前添加 yum/dnf 重试配置（如 `echo 'retries=10' >> /etc/yum.conf` 或 `echo 'timeout=300' >> /etc/yum.conf`），或添加 `--setopt=retries=10` 参数，提高对间歇性网络波动的容错能力。但这只能缓解症状，无法根治上游仓库的 HTTP/2 协议层问题。

## 需要进一步确认的点
1. 该 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）与其他 aarch64 runner 的网络状况是否存在差异——可对比近期同一仓库的其他 aarch64 构建是否也遇到类似 curl error。
2. `repo.openeuler.org` 的 24.03-LTS-SP4 aarch64 仓库是否对 HTTP/2 的支持存在已知 bug（curl error 92 `INTERNAL_ERROR` 通常指向服务端 HTTP/2 实现问题）。
3. 若 retry CI 后问题持续出现，需确认是否需要联系 openEuler 基础设施团队排查仓库 CDN/反向代理的 HTTP/2 配置。
