# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库下载中断
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Stream error, INTERNAL_ERROR, repo.openeuler.org, yum install, MIRROR, No more mirrors to try

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`:4（`RUN yum install -y ...` 步骤）
- 失败原因: CI 构建节点（aarch64）在从 `repo.openeuler.org` 下载 `openEuler-24.03-LTS-SP4` 仓库 RPM 包时遭遇 HTTP/2 传输层错误和 SSL 连接中断，导致 173 个待安装包中的多个发生下载失败。其中 `vim-common` 包在重试所有镜像后仍无法下载，yum 事务因此中断。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据文件，Dockerfile 中的 `yum install` 命令语法和包名正确无误。失败根因是 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在构建时段存在网络层传输问题（HTTP/2 stream 异常、SSL 层读取失败），172/173 个包已成功下载，仅 `vim-common` 因累计失败耗尽所有镜像重试机会。该问题为 CI 基础设施/上游仓库的网络波动，非 PR 代码缺陷。

## 修复方向

### 方向 1（置信度: 中）
**触发重试**。失败属于镜像站临时网络波动导致的偶发 infra-error，最可能的修复方式是重新触发 CI 构建。若 `repo.openeuler.org` 的 SP4 aarch64 仓库在该时段恢复了正常服务，重试即可通过。

### 方向 2（置信度: 低）
**增加 yum 重试/超时配置**。若该问题频繁复现，可在 `yum install` 前添加重试参数（如 `yum install --setopt=retries=10 --setopt=timeout=300 ...`）或在 `yum.conf` 中配置更宽松的重试策略，增加对临时网络波动的容忍度。但这只是缓解措施，不会从根本上解决上游仓库的网络问题。

## 需要进一步确认的点
1. **仓库可用性**：确认 `https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 当前是否可正常访问，以及该仓库近期是否有维护或故障记录。
2. **复现性**：在同一 aarch64 CI runner 上重新触发构建，确认问题是偶发还是持续存在的。
3. **镜像站差异**：检查是否存在 openEuler 24.03-LTS-SP4 的其他镜像站（如华为云镜像站），作为备选下载源以提高可靠性。
4. **SP3 对比**：同一仓库的 brpc SP3 构建是否也出现类似网络问题，以判断该问题是否仅限于 SP4 仓库。
