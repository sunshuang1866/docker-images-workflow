# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库下载不稳
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), OpenSSL SSL_read, SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 556.2  [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2  [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/...kernel-headers-... [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/... [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/... [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install -y ...` 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库 `repo.openeuler.org` 在 CI 构建时段出现 HTTP/2 流传输不稳定，多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）在下载过程中遭遇 Curl error (92)（HTTP/2 流异常中断）和 Curl error (56)（SSL 读取失败）。前三个包在重试后成功下载，但 `vim-common` 耗尽所有镜像重试次数后仍失败，导致整个 `yum install` 命令退出码为 1，Docker 构建中止。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 中的 `yum install` 依赖列表语法正确，所列软件包均为 openEuler 24.03-LTS-SP4 仓库的标准包。失败根因是 CI 构建期间 openEuler 官方仓库服务器端的 HTTP/2 连接不稳定（非客户端或 Dockerfile 问题）。日志显示构建运行在 `ecs-build-docker-aarch64-04-sp`（aarch64 runner）上，仅该架构的仓库出现网络波动。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，触发 CI 重试即可。** 该失败属于临时性基础设施网络波动，openEuler 仓库在同一时段对多个包出现 HTTP/2 流错误。在仓库服务恢复正常后重新触发构建（retry），大几率可通过。Code Fixer 无需处理。

### 方向 2（置信度: 低）
如重试多次仍失败，可在 Dockerfile 的 `yum install` 命令中添加重试参数（如 `--setopt=retries=10`），提高 yum 对网络波动的容忍度。但该方向为降级方案，优先尝试方向 1。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 aarch64 仓库在重试时是否已恢复正常（检查仓库状态页或手动 wget 测试 `vim-common` 包）。
- 如果同一时段多个 PR 的 aarch64 构建均失败，说明仓库侧存在临时故障，等待恢复后批量重试即可。
