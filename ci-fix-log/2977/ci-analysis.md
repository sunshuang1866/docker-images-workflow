# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, MIRROR, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install` 步骤）
- 失败原因: openEuler 官方镜像站 `repo.openeuler.org` 在处理 HTTP/2 请求时多次出现流层协议错误（`Curl error (92)`）和 SSL 连接中断（`Curl error (56)`），涉及 gcc、kernel-headers、perl-MIME-Base64、vim-common 等 4+ 个软件包。yum 在耗尽所有镜像重试后仍无法成功下载 `vim-common`，导致 173 个软件包的安装任务整体失败。

### 与 PR 变更的关联
与 PR 变更无关。PR 新增的 Dockerfile 结构正确，`yum install` 包列表完整且合理（包含了构建 brpc 所需的 gcc、cmake、openssl-devel、gflags-devel、protobuf-devel、leveldb-devel 等）。失败完全由 `repo.openeuler.org` 镜像站的网络/HTTP2 协议层问题引起，属于 CI 基础设施故障。

## 修复方向

### 方向 1（置信度: 高）
此为 CI 基础设施问题（`repo.openeuler.org` HTTP/2 服务端异常），无需修改 PR 代码。触发 CI 重试（re-run）即可。若该镜像站持续出现同类错误，需由 openEuler 基础设施团队排查 `repo.openeuler.org` 的 HTTP/2 协议栈或负载均衡器配置。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段（2026-07-09 13:44-14:09 UTC）是否存在已知的 HTTP/2 服务端异常或 CDN 节点故障。
- 确认重试后问题是否复现：若重试仍失败且错误模式一致，需上报至 openEuler 基础设施团队。
