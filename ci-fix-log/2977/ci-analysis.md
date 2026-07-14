# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像站HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, yum install, MIRROR, No more mirrors to try

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install -y ...` 步骤）
- 失败原因: aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 openEuler 24.03-LTS-SP4 的 RPM 包时遭遇多次 HTTP/2 流中断错误（Curl error 92）和 SSL 连接错误（Curl error 56）。虽有 172 个包下载成功，但 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 在所有镜像重试耗尽后仍失败，导致 yum 退出码 1，Docker 构建中断。

### 与 PR 变更的关联
**与 PR 变更无关**。PR 仅新增了一个标准 Dockerfile 和配套元数据（README.md、image-info.yml、meta.yml）。Dockerfile 中的 `yum install` 安装的是 openEuler 24.03-LTS-SP4 官方仓库的标准开发包，不涉及自定义源或特殊版本。失败根因是上游仓库 `repo.openeuler.org` 在构建时段（2026-07-09 13:45 UTC）对 aarch64 节点的 HTTP/2 连接不稳定，属于上游基础设施瞬时故障。

## 修复方向

### 方向 1（置信度: 高）
**触发重试构建**。上游 RPM 仓库 `repo.openeuler.org` 的网络瞬时波动导致本次下载失败，PR 的 Dockerfile 和元数据内容本身没有问题。在仓库网络恢复稳定后重新触发 CI 构建即可通过。

### 方向 2（置信度: 低）
**若此问题反复出现**，可在 Dockerfile 的 `yum install` 前增加镜像源配置文件，将默认源从 `repo.openeuler.org` 切换为华为云镜像站 `repo.huaweicloud.com/openEuler`，以提高 CI 构建时的网络稳定性。该方案为规避性修复，非根因解决。

## 需要进一步确认的点
- `repo.openeuler.org` 在 2026-07-09 13:45 UTC 时段是否存在已知的服务端问题或网络故障。
- 此失败是否仅在 aarch64 节点出现（本地日志为 aarch64），x86_64 节点上是否正常通过。

## 修复验证要求
无需代码修复。若选择方向 2 进行规避，code-fixer 需验证 `repo.huaweicloud.com/openEuler` 在 aarch64 节点上均可达（HTTP 200），且镜像中 RPM 包版本与 `https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 中的包版本一致。
