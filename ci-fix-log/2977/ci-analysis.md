# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: Yum仓库HTTP/2错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: Dockerfile:4-11（`RUN yum install -y ...` 步骤），发生在 `ecs-build-docker-aarch64-04-sp` (aarch64) 节点
- 失败原因: `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库存在 HTTP/2 协议层错误（`INTERNAL_ERROR`）和 SSL 连接中断（`SSL_ERROR_SYSCALL`），导致 173 个待安装包中的多个包下载中断。其中 gcc、kernel-headers、perl-MIME-Base64 经重试后恢复，但 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 最终下载失败，yum 耗尽所有镜像源后报错退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 brpc 1.16.0 的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中的 `yum install` 命令语法和包列表完全正确。失败完全由 openEuler 官方仓库端的网络/服务问题导致，属于 CI 基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。这是一个纯粹的 CI 基础设施问题——`repo.openeuler.org` 的 24.03-LTS-SP4 aarch64 仓库在构建时存在 HTTP/2 服务端异常。建议：
- 等待仓库服务恢复后重新触发 CI 构建
- 或在 CI 侧为 aarch64 节点的 yum 配置添加 HTTP/1.1 降级（如 `http2=False` 或 `sslverify=False` 临时绕过），但这是 CI 运维层面的操作，不涉及 PR 代码修改

### 方向 2（置信度: 中）
如果仓库持续不稳定，可考虑在 Dockerfile 中为 yum 添加重试机制（如 `yum install --retries 10` 或先执行 `echo 'retries=10' >> /etc/yum.conf`），但这本质上是规避而非修复根因，且不保证解决 HTTP/2 协议层错误。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 aarch64 runner 上的网络连通性和 HTTP/2 服务状态是否已恢复正常
- 检查是否只有 aarch64 仓库存在此问题，还是多架构均受影响（当前日志仅覆盖 aarch64 构建）

## 修复验证要求
无需验证（infra-error，非代码修复）
