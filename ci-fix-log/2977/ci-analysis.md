# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 仓库源网络不稳
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, No more mirrors to try, yum install, repo.openeuler.org, aarch64

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install ...` 步骤）
- 失败原因: CI 在 aarch64 runner 上执行 `yum install` 时，从 `repo.openeuler.org` 下载 RPM 包遭遇多次 HTTP/2 流错误（curl error 92）和 SSL 连接中断（curl error 56）。虽然大部分受影响的包（gcc、kernel-headers、perl-MIME-Base64）通过重试成功下载，但 `vim-common` 耗尽了所有镜像重试后仍失败，导致整个 yum 事务回滚退出。这是一起 **CI 基础设施/网络层问题**，与 PR 代码变更无关。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个标准的 brpc Dockerfile（与已有的 SP3 版本结构一致）和配套的元数据/文档更新。Dockerfile 中的 `yum install` 命令书写的包名均为 openEuler 24.03-LTS-SP4 官方仓库的标准包，语法正确。失败的直接原因是 `repo.openeuler.org` 的 aarch64 SP4 频道在构建时出现了网络不稳定的情况，导致部分 RPM 包下载失败。在日志中，这 173 个包中的绝大多数最终下载成功，仅 `vim-common` 因连续网络故障耗尽重试而失败。

## 修复方向

### 方向 1（置信度: 中）
**重试触发 CI 构建。** 由于这是一起网络层瞬态故障（HTTP/2 流错误为服务端侧连接异常中断），最直接的尝试是重新触发一次 CI 构建。如果仓库源网络恢复，构建应能正常通过。

### 方向 2（置信度: 低）
**如果多次重试均失败**，需排查是否 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 这个具体版本的包在 `repo.openeuler.org` 的 aarch64 SP4 频道中确实存在文件损坏或缺失问题。可手动尝试 wget 该 URL 验证，若确认是包本身问题则需要联系 openEuler 镜像站管理员修复。

## 需要进一步确认的点
- `repo.openeuler.org` 的 aarch64 SP4 频道在构建时间点是否存在服务端 HTTP/2 实现缺陷或网络抖动
- `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 在仓库中是否确实存在且可正常下载
- 同一 PR 的 x86_64 架构构建是否成功（日志仅提供了 aarch64 的失败日志，若 x86_64 构建成功则进一步佐证此为 aarch64 仓库端的局部问题）
