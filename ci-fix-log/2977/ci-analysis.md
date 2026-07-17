# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
------
ERROR: failed to solve: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

在 `vim-common` 最终失败前，多个包在下载过程中也遭遇了类似的 HTTP/2 流错误（gcc、kernel-headers、perl-MIME-Base64），但经过重试后成功下载：
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: Docker 构建在 aarch64 runner 上执行 `yum install` 时，从 `repo.openeuler.org` 下载 173 个 RPM 包，过程中 `repo.openeuler.org` 镜像站的 HTTP/2 连接频繁出现流错误（`INTERNAL_ERROR`）和 SSL 读错误（`SSL_ERROR_SYSCALL`）。虽然大部分包通过 yum 内置重试机制成功下载，但传递依赖 `vim-common` 耗尽所有镜像重试次数后永久失败，导致整个 `RUN` 步骤以 exit code 1 终止。

### 与 PR 变更的关联
PR 新增了 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`（共 25 行）及 3 个元数据文件的条目。Dockerfile 的 `yum install` 命令语法正确、包名有效，失败与 PR 代码变更无关——完全是 openEuler 官方仓库 `repo.openeuler.org` 在构建时刻的 HTTP/2 传输不稳定导致的 **infra-error**。

## 修复方向

### 方向 1（置信度: 中）
由于此次失败是 transient infra 问题，最简单的处理方式是 **触发 CI 重新构建**。同一 Dockerfile 在仓库网络正常时大概率能通过。注意：失败发生在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上，重试时可能被调度到不同节点，但仓库端网络问题也可能持续存在，需观察重试结果。

### 方向 2（置信度: 低）
若重新构建仍然失败，可在 Dockerfile 的 `yum install` 命令前添加 `yum makecache` 或为 `yum install` 增加重试参数（如 `--setopt=retries=10`），提高对瞬态网络错误的容忍度。但这只能缓解、无法根治仓库端 HTTP/2 协议栈的不稳定性。

## 需要进一步确认的点
- `repo.openeuler.org` 的 HTTP/2 服务是否在 aarch64 构建时间段（2026-07-09 13:26-13:45 UTC）存在已知故障或维护窗口
- 同一时间段内其他 PR 的 aarch64 构建是否也出现相同的 HTTP/2 流错误（若其他构建正常，则可能与本 runner 节点网络有关）
- `vim-common` 传递依赖是否可以通过精简 `yum install` 包列表来避免（如检查 `git` 的 `--no-install-recommends` 等效选项）

## 修复验证要求
无需验证。本次失败为 infra-error，与 PR 代码变更无关，PR 中的 Dockerfile 和元数据文件无需修改。
