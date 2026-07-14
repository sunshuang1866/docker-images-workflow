# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler镜像站下载波动
- 新模式症状关键词: Curl error, HTTP/2 stream, INTERNAL_ERROR, repo.openeuler.org, vim-common, No more mirrors to try

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
- 失败原因: CI 构建环境（aarch64 runner `ecs-build-docker-aarch64-04-sp`）在通过 `yum` 从 `repo.openeuler.org` 下载 RPM 包时，多个包遇到 HTTP/2 流中断错误（curl error 92）和 SSL 读取失败（curl error 56）。其中 `gcc`、`kernel-headers`、`perl-MIME-Base64` 等包在重试后下载成功，但 `vim-common` 在耗尽所有镜像重试后仍无法下载，导致整个 `yum install` 步骤失败。

### 与 PR 变更的关联
**与 PR 改动无关。** 本次 PR 仅新增了一个 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）和相关元数据文件（`README.md`、`image-info.yml`、`meta.yml`）。Dockerfile 内容本身正确——`yum install` 命令语法、包名列表均无误。失败发生在 RPM 包下载阶段，根因是 `repo.openeuler.org` 镜像站在该构建时间窗口内存在网络波动（HTTP/2 流异常中断），属于 CI 基础设施问题。其他 SP4 分支的同类 Docker 构建（如已存在的 `24.03-lts-sp4` 镜像）若在同一时段构建，也会遇到相同问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复 —— 重试即可。** 这是 openEuler 官方镜像站 `repo.openeuler.org` 的临时网络波动问题。在 Dockerfile 中多次出现 `Curl error (92)` 和 `Curl error (56)`，且大部分包在重试后成功下载（如 `gcc` 在 `#7 831.9` 处重试成功），仅 `vim-common` 最终失败。建议：等待镜像站恢复后重新触发 CI 构建，大概率会直接通过。

### 方向 2（置信度: 低）
若镜像站持续不稳定，可在 `yum install` 前添加 `yum makecache` 预热缓存，并给 `yum install` 增加 `--setopt=retries=10` 提高重试次数，以增强对临时网络波动的容忍度。但这不是根本解决方案，且从现有 SP3 同类 Dockerfile 来看并非必需。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 镜像站在构建时段（2026-07-09 13:45 UTC 前后）是否存在已知的服务中断或网络波动。
- 确认同批次其他 openEuler 24.03-LTS-SP4 镜像（如 SP4 分支下的其他已存在 Dockerfile）是否也有类似的 `yum` 下载失败，以排除 runner 节点网络问题。

## 修复验证要求
无需代码修复，重试 CI 即可。若重试仍失败且以下两点均满足：(1) 同一 runner 上其他镜像构建也失败，(2) 同一时段其他 runner 上构建成功，则可能为特定 runner 节点网络问题，需联系 CI 基础设施团队排查。
