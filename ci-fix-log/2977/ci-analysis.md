# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2连接中断
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包过程中遭遇多次 HTTP/2 连接中断（Curl error 92: INTERNAL_ERROR）和 SSL 读取失败（Curl error 56: SSL_ERROR_SYSCALL）。多数包在重试后成功下载，但 `vim-common-9.0.2092-36.oe2403sp4.aarch64` 在所有镜像源均重试失败后导致 yum 安装整体退出。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个语法正确的 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）及配套的 README、image-info.yml 和 meta.yml 条目。Dockerfile 中 `yum install` 的包列表正确，所依赖的 RPM 包在 openEuler 24.03-LTS-SP4 仓库中均存在（从日志可见 yum 成功解析了所有 173 个包的依赖关系并开始下载），失败纯粹由 `repo.openeuler.org` 源站在构建时段内的网络/服务端稳定性问题引起。

## 修复方向

### 方向 1（置信度: 高）
**重试即可**。该失败为 `repo.openeuler.org` 软件源在特定时段的 HTTP/2 连接不稳定导致，属于 CI 基础设施层面的瞬时故障。无需修改任何代码或 Dockerfile，重新触发 CI 构建即可。若重试后仍然失败，则需联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 aarch64 仓库服务状态。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段是否有已知的服务降级或维护事件。
- 若多次重试后仍然失败，需排查 CI runner 节点到 `repo.openeuler.org` 的网络链路质量（是否有代理或防火墙干扰 HTTP/2 长连接）。
