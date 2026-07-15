# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像源HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, repo.openeuler.org, No more mirrors to try, yum install

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install ...` 步骤）
- 失败原因: CI 的 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时，多次遭遇 HTTP/2 流错误（`INTERNAL_ERROR` err 2）和 SSL 连接中断（`SSL_ERROR_SYSCALL`），172 个包中有多个包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载失败，最终 vim-common 用尽所有重试 mirror 后报错，导致 `yum install` 退出码为 1，Docker 构建失败。

### 与 PR 变更的关联
与 PR 变更**无关**。PR 新增的 Dockerfile 中 `yum install` 命令语法正确、包名有效，yum 也成功完成了 repository metadata 加载和依赖解析（列出的 173 个包均为 openEuler 24.03-LTS-SP4 仓库中存在的合法包），约 170 个包下载成功。失败纯粹是由于 CI runner 到 `repo.openeuler.org` 的网络在 aarch64 架构线路上不稳定，HTTP/2 连接被服务端异常关闭或 SSL 层发生系统调用错误。属于外部网络因素导致的间歇性故障，重试通常可以解决。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。这是 CI 基础设施网络问题，Code Fixer 无需处理。建议操作：
- 重新触发 CI 构建（retry），网络恢复后构建即可通过。
- 若持续复现，需由 CI 运维团队排查 `ecs-build-docker-aarch64-04-sp` runner 到 `repo.openeuler.org` 的网络质量，或检查 openEuler 镜像站在 aarch64 线的 HTTP/2 服务端配置是否存在异常。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在故障时段是否对 aarch64 线路存在 HTTP/2 服务端问题。
- 确认 CI runner `ecs-build-docker-aarch64-04-sp` 的网络出口是否存在间歇性丢包或 DNS 问题。

## 修复验证要求
不适用 — 此为 infra-error，无需代码修复。
