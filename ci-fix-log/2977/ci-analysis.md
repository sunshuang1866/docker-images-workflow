# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像源下载抖动
- 新模式症状关键词: [MIRROR], Curl error (92), Curl error (56), No more mirrors to try, repo.openeuler.org, vim-common

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ...

#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for ... [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]

#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ...
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:4（`Other/brpc/1.16.0/24.03-lts-sp4/Dockerfile` 第 4-11 行 `RUN yum install -y ...`）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `yum install` 时，`repo.openeuler.org` 镜像站多次出现 HTTP/2 流错误（Curl error 92）和 SSL 读取错误（Curl error 56），导致 `vim-common-9.0.2092-36.oe2403sp4.aarch64` 等 RPM 包下载失败，yum 在所有镜像重试耗尽后放弃，构建中断。

### 与 PR 变更的关联
此失败与 PR 的代码变更**无关**。PR 仅新增了一个符合仓库规范的 Dockerfile（安装标准依赖、clone 源代码、cmake 构建），以及配套的 README.md、image-info.yml、meta.yml 元数据文件。失败的原因是 openEuler 官方 RPM 镜像站在 CI 运行期间出现网络抖动（HTTP/2 流关闭异常），属于 CI 基础设施问题。同样的 Dockerfile 在镜像站恢复后重新触发构建即可通过。

## 修复方向

### 方向 1（置信度: 中）
**重试构建**。此失败为 openEuler 官方镜像站 `repo.openeuler.org` 的网络瞬时不稳定所致（HTTP/2 流错误 + SSL 读取异常），非代码问题。重新触发 CI 构建，镜像站恢复后 yum 包下载应可正常完成。

### 方向 2（置信度: 低）
**添加 yum 重试机制**。若此类镜像站抖动频繁出现，可在 Dockerfile 的 `yum install` 步骤前增加重试逻辑（如 `for i in 1 2 3; do yum install ... && break; done`），但此为可选优化而非必要修复。

## 需要进一步确认的点
- `repo.openeuler.org` 镜像站是否在 CI 构建时段有已知的稳定性问题（如 CDN HTTP/2 连接异常）。
- 确认 x86_64 架构的并行的 CI job 是否也遇到同样问题，以及是否可以单独重新触发 aarch64 job。
- 若重试后问题依旧，需确认 `vim-common-2:9.0.2092-36.oe2403sp4.aarch64` 是否在镜像站确实存在（非 404 问题，本次报错为传输层错误而非 404）。
