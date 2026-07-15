# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: yum镜像站HTTP/2下载失败
- 新模式症状关键词: Curl error (92), HTTP/2 INTERNAL_ERROR, repo.openeuler.org, yum install, No more mirrors to try, SSL_ERROR_SYSCALL

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（yum install 步骤）
- 失败原因: aarch64 runner 上通过 `repo.openeuler.org` 下载 `vim-common` RPM 包时，HTTP/2 连接多次被服务端中断（HTTP/2 INTERNAL_ERROR），yum 镜像重试机制耗尽后面最终失败。构建全程共 4 个包遭遇下载错误（gcc、kernel-headers、perl-MIME-Base64、vim-common），前三者在重试后成功，仅最后下载的 vim-common 无更多镜像可尝试而失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个格式正确的 brpc Dockerfile（依赖安装、源码克隆、cmake 构建）和配套元数据文件。yum install 步骤中的依赖包列表、安装命令语法均无问题，gcc（30 MB）和 kernel-headers 在遭遇相同 HTTP/2 错误后成功重试即证明这一点。失败原因是 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在本次构建期间存在间歇性网络故障（HTTP/2 流中断、SSL 读取异常），属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修复，重试 CI 即可。** 这是 `repo.openeuler.org` 镜像站在 aarch64 构建节点的临时网络故障（HTTP/2 流异常中断）。历史上 `gcc` 包在相同错误下重试成功，说明该仓库本身数据完整、仅传输层不稳定。建议在 PR 下触发 CI 重新运行（re-run），成功的概率很高。

### 方向 2（置信度: 低）
若多次重试仍失败，可考虑在 Dockerfile 的 yum 命令中增加 `--retries` 参数或调整 `mirrorlist` 配置增加重试容忍度。但这属于规避而非根治，且当前所有类似 Dockerfile 均未作此处理，不建议作为常规修复方向。

## 需要进一步确认的点
- `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在 2026-07-09 13:45 UTC 前后的服务状态（是否发生短暂中断或 HTTP/2 协议问题）
- 该 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络质量和 HTTP/2 代理兼容性
