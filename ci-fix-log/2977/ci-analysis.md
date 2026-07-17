# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源下载网络抖动
- 新模式症状关键词: Curl error, HTTP/2 framing layer, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 节点（`ecs-build-docker-aarch64-04-sp`）上构建 Docker 镜像时，`yum install` 从 `repo.openeuler.org` 下载 173 个 RPM 包的过程中，遭遇多次 Curl 网络错误（HTTP/2 stream INTERNAL_ERROR 和 SSL 连接中断）。前三次错误（gcc、kernel-headers、perl-MIME-Base64）在重试后恢复，但 vim-common 最终耗尽所有重试次数，导致 `yum install` 退出码为 1，Docker 构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 内容正确——`yum install` 命令语法无误，所需包名均为 openEuler 24.03-LTS-SP4 仓库中的标准包。失败完全由 openEuler 官方仓库服务器 `repo.openeuler.org` 在构建时段（2026-07-09 13:45 UTC）出现的间歇性 HTTP/2 连接问题导致。同一个 RUN 步骤中，已成功下载了 172/173 个包（日志显示 172 个包已完成下载），仅最后一个包 `vim-common` 因网络问题未完成下载。

## 修复方向

### 方向 1（置信度: 高）
**无需任何代码修改。** 这是 CI 基础设施/上游仓库的临时网络故障。Code Fixer 无需处理 Dockerfile 或任何代码文件。触发 CI 重新运行（retry/rerun）即可，问题大概率已自行恢复。

### 方向 2（置信度: 低，仅在重试持续失败时考虑）
如果多次重试后同一包仍然下载失败，可能说明 `vim-common-2:9.0.2092-36.oe2403sp4.aarch64` 在仓库中确实存在问题（如镜像同步不完整）。此时可考虑从 `yum install` 列表中移除 `vim-common`（它是 git 的弱依赖，对 Docker 构建非必需），但鉴于 172/173 个包均已成功下载，此方向概率极低。

## 需要进一步确认的点
- 无需进一步确认。日志证据充分，错误信息明确为网络层传输问题（Curl error 92/56），且与 PR 代码变更完全无关。

## 修复验证要求
无。本次失败属于 infra-error，Code Fixer 无需任何操作。重新触发 CI 构建以验证问题是否已自行恢复。
