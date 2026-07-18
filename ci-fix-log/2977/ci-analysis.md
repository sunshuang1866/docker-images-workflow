# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler镜像站网络波动
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（yum install 步骤）
- 失败原因: aarch64 构建节点在通过 yum 从 `repo.openeuler.org` 下载 RPM 包时，经历了多次 HTTP/2 流错误（Curl error 92）和 SSL 连接中断（Curl error 56）等网络波动，大部分包在重试后下载成功，但 `vim-common` 在重试耗尽后仍失败，导致整个 yum 事务失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个标准的 brpc 1.16.0 Dockerfile（及其元数据文件），Dockerfile 中的 `yum install` 命令语法和包名均正确无误。失败发生在 Docker 构建的第一步（`yum install` 下载阶段），属于 openEuler 官方镜像仓库 `repo.openeuler.org` 的临时性网络不稳定问题。构建环境为 aarch64（`ecs-build-docker-aarch64-04-sp`），下载的 173 个 RPM 包中绝大多数成功（如 gcc、kernel-headers 均在重试后下载成功），只有最终一个 vim-common 在镜像源重试耗尽后失败。

## 修复方向

### 方向 1（置信度: 高）
**等待基础镜像站恢复后重试 CI。** 这是典型的 infra-error，根源是 `repo.openeuler.org` 的临时性网络波动导致 HTTP/2 流异常中断。Dockerfile 本身无需任何修改。建议在 openEuler 镜像站网络稳定后重新触发 CI 构建（retry job）。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 当前服务状态是否正常（可尝试从外部手动 wget 测试 aarch64 仓库的 RPM 包下载）
- 如果同一 PR 多次重试 CI 均失败且错误一致，则需考虑是否为 openEuler 24.03-LTS-SP4 aarch64 仓库中 `vim-common-9.0.2092-36` 包本身存在问题（如 RPM 元数据损坏导致 HTTP/2 传输异常），此时应向 openEuler 镜像站维护团队报告
