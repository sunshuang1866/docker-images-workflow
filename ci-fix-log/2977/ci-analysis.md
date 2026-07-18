# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: yum源HTTP2传输异常
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, repo.openeuler.org, No more mirrors to try

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 的 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）在从 `repo.openeuler.org` 下载 173 个 RPM 依赖包时，多个包遭遇 HTTP/2 协议层流传输错误（`INTERNAL_ERROR`）和 SSL 连接中断（`SSL_ERROR_SYSCALL`）。171 个包经重试后成功下载，但 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 耗尽所有镜像源重试后彻底失败，导致 `yum install` 退出码为 1，Docker 构建终止。

### 与 PR 变更的关联
**无关**。PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套的 README.md、image-info.yml、meta.yml 元数据文件。Dockerfile 中的 `yum install` 命令语法正确，所列包名均为 openEuler 24.03-LTS-SP4 仓库中的标准包。失败发生在 yum 从 `repo.openeuler.org` 下载 RPM 包的阶段，属于 openEuler 官方镜像源在 aarch64 通道上的网络传输问题，与 PR 代码变更无任何关联。

## 修复方向

### 方向 1（置信度: 高）
此失败属于 CI 基础设施/上游镜像源的瞬时网络故障，**不需要修改 Dockerfile 或任何 PR 代码**。建议操作：
- 等待 `repo.openeuler.org` aarch64 通道的网络状况恢复后，重新触发 CI 构建。
- 如需降低此类问题的概率，可考虑在 Dockerfile 的 `yum install` 命令中添加 `--setopt=retries=10 --setopt=timeout=120` 或类似的重试/超时参数，但这不是必须的。

## 需要进一步确认的点
- 该 aarch64 runner 访问 `repo.openeuler.org` 的网络是否存在持续性问题（DNS 解析、链路丢包等），建议查看该时段 `repo.openeuler.org` 的服务状态或联系基础镜像维护团队确认。
- 若重试后仍失败，需排查是否是 `repo.openeuler.org` 上 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 这一特定包在 CDN 节点上出现文件损坏或分发异常。
