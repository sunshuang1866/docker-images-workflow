# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像下载不稳定
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, [MIRROR], [FAILED], No more mirrors to try, yum install, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`:4（`RUN yum install -y ...` 步骤）
- 失败原因: CI aarch64 runner 在从 `repo.openeuler.org` 下载 173 个 RPM 依赖包时，多个包遭遇 HTTP/2 流错误和 SSL 连接中断。大部分包通过 yum 重试机制下载成功，但 `vim-common-9.0.2092-36.oe2403sp4.aarch64` 在所有镜像重试耗尽后仍下载失败，导致整个 `yum install` 命令以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 改动无关。** 本次 PR 新增的 Dockerfile 中 `yum install` 命令语法正确，所有列出的软件包名均有效（yum 成功解析了完整依赖树并开始下载）。失败属于构建时 `repo.openeuler.org` 镜像站的临时网络不稳定问题，3 个包（gcc、kernel-headers、perl-MIME-Base64）在遇到网络错误后通过重试成功下载，仅 `vim-common` 重试耗尽后最终失败。若重新触发 CI，有较大概率成功。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。这是典型的 CI 基础设施网络波动问题，Dockerfile 本身无需修改。`vim-common` 包在 `repo.openeuler.org` 上确实存在（yum 已解析到该依赖），只是下载过程受网络影响失败。重试 CI 大概率能成功完成构建。

### 方向 2（置信度: 低）
若多次重试仍失败，可在 Dockerfile 的 `yum install` 命令中添加 `--setopt=retries=10 --setopt=timeout=300` 等 yum 重试参数，增加网络波动的容忍度。但这不是根因修复，仅为缓解手段。

## 需要进一步确认的点
- `repo.openeuler.org` 的 aarch64 仓库（`openEuler-24.03-LTS-SP4/OS/aarch64/`）在构建时段是否存在服务端 HTTP/2 实现缺陷或负载过高问题。
- 确认 CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络是否稳定。
- 确认该失败是否仅出现在 aarch64 runner 上，x86_64 runner 是否也存在类似问题。
