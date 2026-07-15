# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库下载网络故障
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 framing layer, SSL_ERROR_SYSCALL, No more mirrors to try, vim-common, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 556.2  [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2  [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 节点（`ecs-build-docker-aarch64-04-sp`）上构建 Docker 镜像时，`yum install` 从 `repo.openeuler.org` 下载 RPM 包过程中遇到多次 HTTP/2 stream error（curl error 92）和 SSL 传输错误（curl error 56）。其中 `gcc`、`kernel-headers`、`perl-MIME-Base64` 等包在重试后成功下载，但 `vim-common` 包因网络错误耗尽了所有镜像源重试次数，最终导致 yum 事务失败。

### 与 PR 变更的关联
**与 PR 无关**。PR 变更仅新增了一个标准的 brpc Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中的 `yum install` 命令语法正确、包名有效。失败完全由 CI 构建节点与 openEuler 官方镜像站之间的网络不稳定导致（HTTP/2 流异常关闭、SSL 连接中断），属于基础设施层面的瞬时故障。

## 修复方向

### 方向 1（置信度: 中）
**触发 CI 重试**。该失败属于 `repo.openeuler.org` 镜像站的瞬时网络/HTTP/2 故障，与 PR 代码无关。在 openEuler 镜像站恢复稳定后，重新触发 CI 流水线即可（可尝试手动触发或推送空 commit 触发 rerun）。

### 方向 2（置信度: 低）
若重试后仍然频繁出现同类错误，可考虑在 Dockerfile 的 yum 命令中添加 `--retries` 参数或使用 `curl` 重试机制预处理关键大包，但这是基础设施层面的 workaround，非根本解决方案。

## 需要进一步确认的点
- openEuler 官方镜像站 `repo.openeuler.org` 在当时是否存在服务端 HTTP/2 或 SSL 层问题（可通过在 CI 构建日志时间点独立 curl 测试确认）
- 该 aarch64 构建节点 `ecs-build-docker-aarch64-04-sp` 的网络环境是否存在间歇性丢包或 HTTP/2 代理兼容性问题
