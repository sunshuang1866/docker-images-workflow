# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler 仓库网络抖动
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, MIRROR, No more mirrors to try, Error downloading packages, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 构建节点 `ecs-build-docker-aarch64-04-sp` 在通过 `repo.openeuler.org` 下载 `24.03-LTS-SP4` 的 aarch64 RPM 包（共 173 个）时，多次遭遇 HTTP/2 协议层错误（`INTERNAL_ERROR` 流异常关闭）和 SSL 连接中断（`SSL_ERROR_SYSCALL`），最终 `vim-common-9.0.2092-36` 包因所有镜像源重试耗尽而下载失败。大多数受影响的包通过 dnf/yum 内置的自动重试机制成功恢复，但 `vim-common` 的下载在达到重试上限后仍失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的改动（新增 Dockerfile、更新 README.md、image-info.yml、meta.yml）均为标准的镜像添加操作，Dockerfile 中 `RUN yum install -y ...` 的包列表（git、gcc、gcc-c++、make、cmake、openssl-devel、gflags-devel、protobuf-devel、leveldb-devel、snappy-devel、abseil-cpp-devel）规范且完整。失败纯粹是由 openEuler 官方 RPM 仓库 `repo.openeuler.org` 在构建时段内的网络不稳定（HTTP/2 连接异常）导致的，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重新触发 CI 构建即可。** 该失败是 `repo.openeuler.org` 仓库服务端的瞬时网络故障，与 PR 代码无关。在仓库服务恢复后重试构建应能正常通过。建议等待网络恢复后重新触发 aarch64 架构的 CI 构建任务。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段的 aarch64 包服务是否正常（可通过浏览器或 curl 直接访问报错 URL 验证）
- 如果是 `repo.openeuler.org` 持续不稳定，考虑为 openEuler 24.03-LTS-SP4 的 aarch64 yum 仓库配置备用镜像源（如华为云镜像站 `repo.huaweicloud.com`），以增加容错能力

## 修复验证要求
（无需填写：该失败为 infra-error，无需修改任何代码文件。）
