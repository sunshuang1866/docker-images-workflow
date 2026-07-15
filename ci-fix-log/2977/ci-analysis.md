# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Yum仓库镜像下载失败
- 新模式症状关键词: Curl error, MIRROR, No more mirrors to try, repo.openeuler.org, yum install, HTTP/2, SSL_ERROR_SYSCALL

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
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上执行 `yum install` 时，`repo.openeuler.org` 仓库镜像多次出现 HTTP/2 stream 错误（Curl error 92）和 SSL 读取错误（Curl error 56），导致 gcc、kernel-headers、perl-MIME-Base64、vim-common 等多个 RPM 包下载失败。最终 vim-common 包耗尽所有镜像重试后仍无法下载，yum 安装失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 这是一个纯粹的 CI 基础设施/网络问题。PR 新增的 Dockerfile 中 `yum install` 命令语法正确，所列软件包（git、gcc、gcc-c++、make、cmake、openssl-devel、gflags-devel、protobuf-devel、protobuf-compiler、abseil-cpp-devel、leveldb-devel、snappy-devel）均为 openEuler 24.03-LTS-SP4 仓库中的标准包。失败发生在 RPM 包的网络下载阶段，而非包依赖解析或安装阶段，属于仓库镜像服务器端的 HTTP/2 连接不稳定。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 此失败为 `repo.openeuler.org` 仓库镜像的瞬时网络波动导致，属于 infra-error。Dockerfile 本身无需任何修改。触发 CI 重新构建即可，若仓库服务恢复，构建应能通过。

### 方向 2（置信度: 低）
**若重试持续失败**，考虑在 Dockerfile 的 `yum install` 命令前添加 `--retries` 或重试逻辑（如将 `yum install` 放入循环重试），或切换至备用镜像源。但这仅作为仓库服务长期不稳定的降级方案，优先建议等待仓库恢复后重试。

## 需要进一步确认的点
1. `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库在 CI 运行时段是否存在服务异常或维护窗口。
2. CI 的 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络链路是否稳定。
3. 若多次重试后仍然失败，需确认 openEuler 24.03-LTS-SP4 仓库中 vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm 是否实际存在且可被正常下载。
