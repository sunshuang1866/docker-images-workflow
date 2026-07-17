# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 官方仓库网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 framing layer, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install ...` 步骤）
- 失败原因: Docker 镜像构建阶段，aarch64 runner 从 `repo.openeuler.org` 下载 RPM 包时遭遇多次 HTTP/2 协议层错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接中断（Curl error 56: SSL_ERROR_SYSCALL），最终 `vim-common` 包耗尽所有镜像重试后下载失败，yum 事务整体回滚

### 与 PR 变更的关联
**与 PR 无关**。PR 仅新增了一个标准 Dockerfile（安装 brpc 1.16.0 相关依赖）和三个元数据文件的更新。Dockerfile 中 `yum install` 的包名和命令语法均正确无误（日志中 `Dependencies resolved` 后列出了 173 个待安装包，解析阶段成功）。所有错误均发生在包下载阶段，是由 openEuler 官方软件仓库 `repo.openeuler.org` 的 HTTP/2 服务端不稳定性或网络链路波动导致的临时性基础设施故障。

### 影响范围
- 影响架构: aarch64（日志显示 runner 为 `ecs-build-docker-aarch64-04-sp`，使用 `docker-build-aarch64` 标签）
- 失败的包: 多个包遇到 transient error（gcc、kernel-headers、perl-MIME-Base64 均在重试后成功），仅 `vim-common` 最终下载失败
- 171/173 个包已成功下载，仅最后一个包失败导致整个 yum 事务回滚

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。此失败为 `repo.openeuler.org` 仓库的临时性网络波动导致，与 PR 代码变更无关。建议等待仓库恢复后重新触发 CI 构建（retry），大概率可以通过。如频繁出现此问题，可考虑在 Dockerfile 的 `yum install` 命令前添加 `yum makecache` 或增加 `--retries` 参数（`echo 'retries=10' >> /etc/yum.conf`）以提高对网络波动的容忍度。

## 需要进一步确认的点
- x86_64 架构构建是否也受影响（日志仅包含 aarch64 架构的构建过程）
- `repo.openeuler.org` 的 aarch64 仓库在构建时段是否存在已知的服务端问题或维护窗口
- 该 runner（`ecs-build-docker-aarch64-04-sp`）的历史构建成功率，以排除 runner 自身网络问题

## 修复验证要求
无需验证。此失败为基础设施问题，Code Fixer 无需提交代码修改。
