# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像仓库网络故障
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: CI 在 aarch64 节点上构建时，`repo.openeuler.org` 镜像站出现 HTTP/2 流错误（`Curl error (92)`）和 SSL 连接中断（`Curl error (56)`），导致多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载失败，其中 `vim-common` 重试所有镜像均失败后 `yum install` 报错退出。

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了一个标准的 Dockerfile 和配套元数据文件（README.md、image-info.yml、meta.yml），均为 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的正常构建描述。Dockerfile 内的 `yum install` 命令格式与同类文件（如 `sp3` 版本对应的 Dockerfile）一致，失败完全由 CI 构建环境的网络问题引起——`repo.openeuler.org` 在 aarch64 节点上对外提供 RPM 包下载时出现间歇性 HTTP/2 流错误。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码**。这是一个 CI 基础设施网络问题（`infra-error`），Code Fixer 无需处理。等待镜像站网络恢复后，重新触发 CI 构建即可。如果问题持续出现，需由 CI 运维团队排查 `repo.openeuler.org` 镜像站的 HTTP/2 服务是否在 aarch64 节点所在网络环境中存在稳定性问题。

## 需要进一步确认的点
- 无需进一步确认。日志证据充分：Curl HTTP/2 流错误和 SSL 连接中断明确指向网络层面，与 PR 代码变更无关。
