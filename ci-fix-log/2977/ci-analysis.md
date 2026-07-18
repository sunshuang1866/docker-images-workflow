# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, SSL_ERROR_SYSCALL, Curl error (56), No more mirrors to try, yum install

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: openEuler 官方仓库 `repo.openeuler.org` 在 aarch64 构建节点上出现 HTTP/2 流传输错误和 SSL 连接中断，导致多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载失败，最终 vim-common 在所有镜像源重试后仍无法下载，yum 安装步骤失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 本身语法正确、包名有效（gcc、gcc-c++、cmake、openssl-devel、gflags-devel、protobuf-devel、abseil-cpp-devel、leveldb-devel、snappy-devel 在日志中均正常列出并进入下载队列）。失败根因是构建时 openEuler 24.03-LTS-SP4 aarch64 仓库服务器端网络不稳定（HTTP/2 INTERNAL_ERROR 和 SSL 连接断开均为服务端问题），属于 CI 基础设施临时故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码**。该失败为 openEuler 官方仓库 `repo.openeuler.org` 的 aarch64 镜像源临时网络故障，与 Dockerfile 内容无关。应触发 CI 重试（re-run），等待仓库服务恢复后构建即可通过。

由于 yum 本身有重试机制（已自动尝试了多个 mirror），但仍全部失败，说明该时间窗口内仓库 aarch64 节点的网络状况确实不稳定。换一个时间段重试通常可以成功。

## 需要进一步确认的点
- 无需进一步确认。日志清晰表明是 openEuler 官方仓库 HTTP/2 流中断导致的 RPM 下载失败，多包同时出现 Curl error (92) 和 Curl error (56)，排除单个包损坏或 PR 代码问题。
- 若多次重试仍然失败，可能需要检查 CI aarch64 构建节点 (`ecs-build-docker-aarch64-04-sp`) 到 `repo.openeuler.org` 的网络连通性，或考虑在 Dockerfile 中配置备用镜像源。

## 修复验证要求
无需验证。该失败为 infra-error，不是代码问题，Code Fixer 无需执行任何修复操作。
