# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库镜像网络抖动
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, Error downloading packages, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]

#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]

#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c yum install -y         git gcc gcc-c++ make cmake which         openssl-devel         gflags-devel         protobuf-devel protobuf-compiler         abseil-cpp-devel         leveldb-devel snappy-devel &&     yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（yum install 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上构建镜像时，从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时遭遇镜像站网络不稳定，多个包（gcc、kernel-headers、perl-MIME-Base64、vim-common）出现 HTTP/2 流错误（Curl error 92）和 SSL 连接中断（Curl error 56）。yum 在尝试所有可用镜像后仍无法成功下载 `vim-common` 包，导致 yum install 命令失败（exit code: 1）。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个格式规范的 Dockerfile（以及配套的 README.md、image-info.yml、meta.yml 元数据更新）。Dockerfile 中的 `yum install` 命令语法正确，所列的软件包（git, gcc, gcc-c++, make, cmake, openssl-devel, gflags-devel, protobuf-devel, protobuf-compiler, abseil-cpp-devel, leveldb-devel, snappy-devel）均为 openEuler 24.03-LTS-SP4 官方仓库中的标准包，失败纯粹由镜像站 `repo.openeuler.org` 的网络不稳定导致，与代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试即可。** 该失败是 openEuler 官方镜像站 `repo.openeuler.org` 在 aarch64 runner 上的网络临时抖动（HTTP/2 流错误）导致的 RPM 包下载失败，属于 CI 基础设施问题。建议在 CI 流水线中重新触发本次构建（re-run/retry），大概率可以通过。

### 方向 2（置信度: 中）
如果反复重试仍失败，可能是 openEuler 24.03-LTS-SP4 aarch64 仓库的特定镜像节点存在持续性问题。可以尝试在 Dockerfile 的 yum install 之前先对 yum 配置进行镜像源调优（如禁用 HTTP/2 或指定备用镜像），但这属于基础设施层面的临时 workaround，不建议作为长期修复方案。

## 需要进一步确认的点
- 确认 openEuler 24.03-LTS-SP4 aarch64 仓库 `repo.openeuler.org` 在 CI 构建时段是否存在已知的镜像服务降级或维护公告。
- 验证其他基于 openEuler 24.03-LTS-SP4 的新增镜像 PR 在相同 aarch64 runner 上是否也遭遇了类似的网络问题（判断是系统性故障还是偶然事件）。
- 确认 vim-common 作为 yum 的事务性依赖引入（被 git 的弱依赖链间接引入），是否可以在 Dockerfile 中显式安装 `vim-common` 使其在一开始就被下载，避免在下载序列末尾因网络波动失败导致全量重试。

## 修复验证要求
不适用。该失败为 infra-error，无需代码修复。
