# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库镜像HTTP/2传输错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Stream error, vim-common, aarch64, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install` 步骤）
- 失败原因: aarch64 构建节点上 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 仓库镜像在执行 yum install 时出现多次 HTTP/2 传输层错误（Curl error 92: HTTP/2 stream INTERNAL_ERROR），gcc、kernel-headers、perl-MIME-Base64 等包虽经重试后下载成功，但 vim-common 包最终耗尽所有镜像重试次数而失败，导致整个 yum install 步骤退出码为 1。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个标准格式的 Dockerfile（`Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`）、README 条目、image-info.yml 条目和 meta.yml 条目，均为合法的元数据变更。Dockerfile 中的 yum install 命令格式与同仓库中其他 24.03-lts-sp4 镜像（如 SP3 版本）一致，所安装的软件包（gcc、cmake、openssl-devel 等）在依赖解析阶段均已成功列出且版本号有效。失败纯粹由 openEuler 官方仓库的 aarch64 镜像服务器 HTTP/2 连接中断导致。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 此失败为临时性基础设施问题（`repo.openeuler.org` 镜像站 HTTP/2 传输层间歇性错误），并非代码缺陷。多数受影响的包（gcc、kernel-headers、perl-MIME-Base64）在 yum 自动重试后下载成功，仅 vim-common 因重试次数耗尽而失败。重新触发 CI 即可大概率通过。

### 方向 2（置信度: 低）
若重新触发 CI 后仍然失败，可检查是否 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库存在持续性问题，或考虑在 Dockerfile 的 yum install 前添加 `echo "retries=10" >> /etc/yum.conf` 增加重试次数以应对间歇性网络波动。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库当前是否可用（可在本地手动 `curl` 测试 vim-common 包的下载）
- 确认 CI 的 aarch64 runner 节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络连接是否存在持续性问题
