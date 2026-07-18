# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像站下载失败
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org, yum install failed

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install` 步骤）
- 失败原因: CI aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 仓库的 173 个 RPM 软件包时，多个包遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接中断（Curl error 56），其中 `vim-common` 包在所有镜像重试后仍下载失败，导致整个 `yum install` 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 代码变更无关。** 本次 PR 仅新增了一个标准的 brpc Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中 `yum install` 的软件包列表与同类镜像（如 `24.03-lts-sp3` 版本）完全一致，均为 openEuler 官方仓库提供的标准包。失败发生在 yum 从远程仓库下载 RPM 包的阶段，是 CI 构建环境与 `repo.openeuler.org` 之间的网络连接问题。

具体观察：
- 173 个包中 172 个最终下载成功（包括前期失败的 gcc、kernel-headers、perl-MIME-Base64 在重试后恢复），仅 `vim-common` 最终耗尽重试次数
- 错误类型均为网络层面的 Curl/SSL 错误，而非包不存在（404）或依赖冲突等仓库内容问题
- 该 Dockerfile 本身结构和包依赖声明无任何问题

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，重试 CI 构建即可。** 这是 `repo.openeuler.org` 的 aarch64 仓库在 CI 构建时的临时性网络波动问题。`vim-common` 包本身存在于仓库中，只是下载过程中 HTTP/2 连接不稳定导致失败。建议在仓库网络状况稳定后重新触发 CI 构建。

## 需要进一步确认的点
- 若有多次重试 CI 均出现相同错误，则需要排查 CI aarch64 构建节点与 `repo.openeuler.org` 之间的网络路由或 CDN 节点是否存在持续性问题
- 若仅 `vim-common` 包持续下载失败而其他包正常，可进一步核查该特定包在 openEuler 24.03-LTS-SP4 aarch64 仓库中是否存在或是否有损坏
