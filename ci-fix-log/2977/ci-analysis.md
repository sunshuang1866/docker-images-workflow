# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件仓库下载不稳定
- 新模式症状关键词: Curl error, HTTP/2, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors, repo.openeuler.org, yum install

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
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI aarch64 构建节点在通过 yum 从 `repo.openeuler.org` 下载依赖包时遭遇了多次网络传输错误（HTTP/2 流中断、SSL 连接异常），其中 gcc、kernel-headers 等包在重试后成功，但 vim-common 在所有镜像源重试均告失败后导致整个 yum 事务失败

### 与 PR 变更的关联
**与 PR 无关。** PR 变更仅新增了一个符合仓库规范的 brpc Dockerfile、更新了 README、image-info.yml 和 meta.yml。Dockerfile 中的 `yum install` 命令所安装的包均为 openEuler 24.03-LTS-SP4 仓库中的标准包，包名和安装语法均正确。该失败是 `repo.openeuler.org` 在 aarch64 架构上的偶发性网络/服务不稳定性导致的，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修复 PR 代码。** 直接在 CI 中重新触发构建（retry）。该失败是 openEuler 软件仓库在构建时段的临时网络抖动（HTTP/2 流中断、SSL 连接异常），多发生在 aarch64 节点上。重新触发后大概率可通过。

### 方向 2（置信度: 中）
如果重试多次仍然失败，可在 Dockerfile 的 `yum install` 命令中添加 `--retries 10` 或 `--setopt=retries=10` 参数，提高 yum 对瞬时网络故障的容忍度。但当前证据表明这属于临时性仓库问题，参数加固可作为降低未来偶发失败概率的兜底手段，非当前 PR 必需。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 aarch64 上的可用性是否近期存在不稳定的已知问题（向 openEuler 基础设施团队确认）
- 检查同一时段其他使用 `openeuler:24.03-lts-sp4` 基础镜像的 PR 是否也有类似下载失败，以判定是系统性仓库故障还是偶发事件
- 检查 x86_64 架构（amd64）的构建是否通过，因为日志仅提供了 aarch64 runner 上的失败信息
