# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: yum仓库下载网络故障
- 新模式症状关键词: Curl error, HTTP/2 framing layer, INTERNAL_ERROR, SSL_ERROR_SYSCALL, repo.openeuler.org, No more mirrors to try, yum install

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: CI aarch64 构建节点在执行 `yum install` 从 `repo.openeuler.org` 下载 RPM 包时，多个包遭遇网络传输异常——HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接中断（Curl error 56: SSL_ERROR_SYSCALL），最终 `vim-common` 包在所有镜像源重试耗尽后仍下载失败，导致 yum 事务中断。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 该 PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 内容本身语法正确、依赖声明合理。失败发生在 Docker 构建的第 2/6 步（`yum install` 阶段），根因是 openEuler 官方软件仓库 `repo.openeuler.org` 对 CI aarch64 构建节点的网络服务不稳定，属于 CI 基础设施层面的瞬态故障。同样的 Dockerfile 在仓库网络恢复后应能正常构建通过。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，重试 CI 即可。** 本次失败为 CI 基础设施网络问题，PR 中新增的 Dockerfile 和相关配置均正确。建议在 `repo.openeuler.org` 网络恢复后重新触发 CI 构建（可通过 `/retest` 或提交空 commit 触发）。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 仓库对 aarch64 架构 RPM 包的服务状态是否正常（可从 CI 节点手动 `curl -I` 验证）。
- 确认 CI 构建节点到 `repo.openeuler.org` 的网络连通性和路由是否存在间歇性问题。
