# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络故障
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum install, aarch64

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install` 步骤，Docker build 阶段 #7）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `yum install` 时，`repo.openeuler.org` 镜像站对多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）返回 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接中断错误（Curl error 56），最终 `vim-common` 包在所有镜像重试后仍下载失败，导致整个 `yum install` 步骤以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml）。Dockerfile 的 `yum install` 命令本身语法正确、包名有效（日志显示 Dependencies resolved 成功，173 个包中有 172 个已成功下载，仅最后一个 `vim-common` 因网络故障失败）。失败完全由 `repo.openeuler.org` 镜像站的网络/服务端问题导致，与 PR 改动无关。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 此失败为 CI 基础设施问题（openEuler 官方镜像站在构建时段出现 HTTP/2 服务端异常），Code Fixer 无需处理。建议：
- 等待镜像站恢复后重新触发 CI 构建（retry）
- 如持续出现，可考虑在 Dockerfile 的 `yum install` 步骤前添加 `--retries` 参数或配置备用镜像源，但这不是代码缺陷

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在当前时段是否已恢复正常（可通过浏览器或 curl 直接访问该 URL 测试）
- 确认该 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否正常
- 如问题持续，确认是否是 `repo.openeuler.org` 的 HTTP/2 服务端配置问题（多个不同包的 stream 均出现 INTERNAL_ERROR）
