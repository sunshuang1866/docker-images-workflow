# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源HTTP/2连接异常
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, yum install, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

此外，在 vim-common 最终失败前，另有 3 个包也遭遇了相同的 HTTP/2 流错误，但均在重试后成功下载：
- `gcc-12.3.1-110.oe2403sp4.aarch64.rpm` — Curl error (92) 后重试成功
- `kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm` — Curl error (92) 后重试成功
- `perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm` — Curl error (56, SSL_ERROR_SYSCALL) 后重试成功

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install ...` 步骤）
- 失败原因: openEuler 官方软件源 `repo.openeuler.org` 在 aarch64 构建环境中出现间歇性 HTTP/2 连接异常（Curl error 92: `HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），导致 173 个待安装包中的最后一个（`vim-common`）在多次重试后仍下载失败，yum 安装步骤整体失败。该问题与 PR 代码变更完全无关。

### 与 PR 变更的关联
**无关联。** 本次 PR 仅新增了一个标准 Dockerfile（安装 openEuler 官方仓库中的系统包）和 3 个元数据/文档文件的更新。Dockerfile 中的 `yum install` 命令语法正确，所列软件包均为 openEuler 24.03-LTS-SP4 官方仓库中的标准包（gcc、gcc-c++、make、cmake、openssl-devel 等）。失败由 CI 构建时 openEuler 软件源 `repo.openeuler.org` 的网络不稳定导致，与 PR 的任何改动无关。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建**。该失败为 transient 网络问题（openEuler 软件源 HTTP/2 连接间歇性异常），大概率在重新构建时不再复现。若多次重试仍失败，则需联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 aarch64 镜像服务状态。

### 方向 2（置信度: 低）
若重试持续失败，可在 Dockerfile 的 `yum install` 前添加 `retries` 和 `timeout` 配置以提升对镜像源间歇性故障的容错能力（如设置 `echo 'retries=10' >> /etc/yum.conf && echo 'timeout=300' >> /etc/yum.conf`），但这属于治标不治本的手段。

## 需要进一步确认的点
- openEuler 官方软件源 `repo.openeuler.org` 在 2026-07-09 13:44–14:07 UTC 期间的 aarch64 仓库服务是否存在异常（需联系 openEuler 基础设施团队确认）
- 该 aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络连接质量是否稳定
- 其他同期构建的 SP4 aarch64 镜像是否也遭遇了相同类型的 Curl error 92 错误
