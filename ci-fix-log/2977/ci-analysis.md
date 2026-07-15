# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, No more mirrors to try, repo.openeuler.org, yum install, aarch64

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建时，`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库多次返回 HTTP/2 流协议错误（curl error 92: `Stream error in the HTTP/2 framing layer`）和 SSL 连接断开（curl error 56）。虽然 gcc、kernel-headers 等大型包通过重试机制成功下载，但作为最后下载的 `vim-common` 包在首次下载失败后所有镜像源均已耗尽，yum 最终报错退出。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了一个结构正确的 Dockerfile（`yum install` 安装依赖的方式与其他 brpc Dockerfile 完全一致）及配套的 README、image-info.yml、meta.yml 条目。失败原因为 openEuler 24.03-LTS-SP4 aarch64 仓库服务器的 HTTP/2 协议层面不稳定，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 这是 `repo.openeuler.org` 镜像站的临时性 HTTP/2 协议问题，不是代码问题。重新触发一次构建（retry / re-run），待仓库服务器稳定后，yum 即可正常下载所有 RPM 包并完成 Docker 镜像构建。不需要对 Dockerfile 或任何代码文件做修改。

### 方向 2（置信度: 低）
如果多次重试后 vim-common 包仍然无法下载，可能需要在 Dockerfile 的 `yum install` 命令中增加 `--setopt=retries=10` 或 `--setopt=timeout=120` 参数，增加下载重试次数和超时时间，以应对仓库服务器的间歇性不稳定。但鉴于日志中 gcc（30 MB）和 kernel-headers（1.7 MB）均通过重试成功下载，这更可能是临时性的服务端问题而非需要客户端侧调优。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库当前是否处于维护或不可用状态（可通过浏览器或 curl 直接访问该 URL 验证）
- 确认该构建失败是否为偶发性（若同一 PR 在 x86-64 架构上构建成功，可进一步佐证这是 aarch64 仓库的临时问题）
- 确认 vim-common 包本身在 SP4 aarch64 仓库中是否真实存在（非 404，只是下载被 HTTP/2 流错误中断）
