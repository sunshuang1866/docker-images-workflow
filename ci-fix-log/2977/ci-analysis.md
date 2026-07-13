# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, No more mirrors to try, yum install

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: aarch64 构建节点在通过 `yum` 从 `repo.openeuler.org` 下载 173 个 RPM 包时，`repo.openeuler.org` 镜像站频繁出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）和 SSL 读取失败（Curl error 56）。其中 `gcc`、`kernel-headers`、`perl-MIME-Base64` 三个包在重试后下载成功，但 `vim-common` 耗尽所有重试次数后仍失败，导致 `yum install` 整体报错退出。

### 与 PR 变更的关联

**与 PR 改动无关。** 该 PR 新增的 Dockerfile 语法正确——`yum install` 在依赖解析阶段已成功列出全部 173 个待安装包，说明包名、仓库源配置均无问题。失败完全由 `repo.openeuler.org` 镜像站在构建时段的网络服务质量不稳定导致，属于 CI 基础设施问题，重新触发构建大概率可自行通过。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重新触发 CI 构建。** 该失败是 openEuler 官方镜像站在 aarch64 构建节点的临时网络抖动所致。同一时段内 4 个包出现 HTTP/2 流错误，其中 3 个在重试后自动恢复，仅 `vim-common` 因重试次数耗尽而失败。可在 CI 中手动 re-run 该 job。

### 方向 2（置信度: 中）
若重复触发仍失败，可在 Dockerfile 的 `yum install` 命令中增加重试参数（如 `--setopt=retries=10` 或 `--setopt=timeout=120`）以提高网络容错能力，但此修改并非必须，属于加固措施。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 `openEuler-24.03-LTS-SP4` aarch64 仓库的镜像站当前网络状态是否正常。
- 确认 CI aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否稳定。
- 若重新触发后仍然失败，需排查是否为特定时间段（日志显示 2026-07-09 13:44 UTC 左右）镜像站存在大规模服务降级。

## 修复验证要求
无需代码修复，重新触发 CI 构建并确认 `yum install` 步骤通过即可。
