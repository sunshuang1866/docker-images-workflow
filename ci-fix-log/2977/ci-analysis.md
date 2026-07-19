# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 stream, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（yum install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库（`repo.openeuler.org`）在 aarch64 构建期间出现网络波动，多个 RPM 包下载遭遇 HTTP/2 流中断（Curl error 92）和 SSL 连接重置（Curl error 56）。虽然大部分包在 yum 重试后成功下载（172/173），但 `vim-common-2:9.0.2092-36.oe2403sp4.aarch64` 耗尽了所有可用镜像重试次数，最终下载失败导致整个 `yum install` 命令返回 exit code 1。

### 与 PR 变更的关联
**完全无关。** PR 仅新增了 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile` 及其元数据文件，Dockerfile 中的 `yum install` 命令写法标准、依赖声明正确。该失败属于 CI 构建环境中 `repo.openeuler.org` 仓库的瞬时网络故障，重试构建即可恢复。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，直接触发 CI 重试。** 该失败为 `repo.openeuler.org` 仓库瞬时网络问题，所有失败均为 HTTP/2 流中断或 SSL 连接重置，属于服务端或中间网络链路的暂时性故障。172/173 个包成功下载也进一步证明 yum install 命令本身无问题。重新触发 CI 构建大概率会成功。

### 方向 2（置信度: 低，仅在反复出现时考虑）
若该镜像 `vim-common` 频繁在 openEuler 24.03-LTS-SP4 的 aarch64 仓库中出现下载失败，可在 Dockerfile 的 yum 命令中增加重试机制（如 `yum install --setopt=retries=10 ...`），或考虑在 `yum install` 中添加 `--skip-broken` 并单独重试失败包。但当前证据显示这仅为一次瞬时故障，不建议先做此类修改。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段（2026-07-09 13:44 UTC 左右）是否存在已知的服务中断或网络波动。
- 确认 aarch64 构建节点 `ecs-build-docker-aarch64-04-sp` 到 `repo.openeuler.org` 的网络链路是否有偶发性丢包或 HTTP/2 协议兼容问题。
