# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: 镜像站网络波动
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 stream, INTERNAL_ERROR, SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败原因: aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）在通过 yum 从 `repo.openeuler.org` 下载 RPM 包时，多次遇到 HTTP/2 流中断（Curl error 92: INTERNAL_ERROR）和 SSL 读取失败（Curl error 56: SSL_ERROR_SYSCALL），重试耗尽后 `vim-common` 包下载失败，导致整个 yum install 步骤退出码 1。

### 与 PR 变更的关联
PR 变更仅为新增一个 brpc 1.16.0 的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中的 `yum install` 命令使用的均为 openEuler 24.03-LTS-SP4 仓库中的标准包名，语法和逻辑无异常。构建失败由 `repo.openeuler.org` 镜像站在构建时段内的网络服务质量波动（HTTP/2 连接异常中断）引发，**与 PR 代码变更无关**。

## 修复方向

### 方向 1（置信度: 中）
此为暂态基础设施故障，非代码缺陷。建议触发 CI 重试（retry），观察是否能在网络正常的时段通过。如多次重试均在同一节点/同一仓库失败，则需要：
- 检查该 aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络连通性；
- 确认 `repo.openeuler.org` 的 HTTP/2 服务和 CDN 节点在当时的健康状态。

### 方向 2（置信度: 低）
如该 aarch64 节点长期无法稳定访问 `repo.openeuler.org`，可考虑在 yum 仓库配置中增加国内镜像源（如 `repo.huaweicloud.com/openeuler`）作为备用镜像，或配置 yum 的 `retries` / `timeout` 参数以提高容错能力。但此方向需由 CI 基础设施团队评估，不在此 PR 范围内。

## 需要进一步确认的点
- 确认同一时段其他 PR（使用同一 aarch64 节点或同一 `repo.openeuler.org` 仓库）是否也出现类似网络错误，以判断是节点问题还是镜像站全局问题；
- 确认本次失败前是否有相邻成功的构建，以排除该节点近期网络配置变更的可能性。

## 修复验证要求
无。此次失败为 infra-error，Code Fixer 无需处理。
