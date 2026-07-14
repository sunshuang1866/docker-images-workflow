# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库HTTP/2下载中断
- 新模式症状关键词: Curl error, HTTP/2 stream, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（yum install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库（`repo.openeuler.org`）在 aarch64 CI runner 构建期间出现间歇性 HTTP/2 连接故障，导致 4 个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载过程中出现 `INTERNAL_ERROR` 或 `SSL_ERROR_SYSCALL`。其中前 3 个包重试后成功，`vim-common` 耗尽所有镜像后失败，最终 yum 整体返回 exit code 1。

### 与 PR 变更的关联
**与 PR 改动无关。** PR 仅新增了一个标准格式的 Dockerfile（安装依赖 → git clone brpc → cmake 构建）及配套的 README、image-info.yml、meta.yml 元数据更新。Dockerfile 语法正确，`yum install` 包列表均有效。失败完全由 openEuler 官方仓库的网络服务端 HTTP/2 协议异常引起，属于 CI 基础设施层面的临时性问题。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。这是 `repo.openeuler.org` 仓库服务的临时性网络故障，PR 代码本身无任何问题。Code Fixer 无需修改任何文件，直接触发 CI 重新运行即可。如果多次重试仍失败，可考虑在 Dockerfile 的 yum 命令前添加重试逻辑或切换镜像源。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在当日是否有已知的服务中断或维护事件。
- 如果多次重试均失败，需要排查 aarch64 CI runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络连通性是否稳定。
