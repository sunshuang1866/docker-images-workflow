# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM仓库网络抖动
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: CI 在 aarch64 runner 上构建镜像时，从 `repo.openeuler.org` 下载 RPM 包过程中遭遇多次 HTTP/2 流错误（Curl error 92）和 SSL 读取错误（Curl error 56），最终 `vim-common` 包因所有镜像源均已尝试失败而无法下载，导致 `yum install` 步骤以退出码 1 失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 该 PR 仅新增了一个标准 Dockerfile（安装 brpc 编译依赖），其中 `yum install` 命令列的包名均为 openEuler 24.03-LTS-SP4 仓库中的合法包名。失败原因是 `repo.openeuler.org` 的 HTTP/2 服务端在下载过程中出现了多次流中断（INTERNAL_ERROR），属于 openEuler 官方镜像仓库的网络/服务端基础设施问题，与 Dockerfile 代码内容或软件包选择无关。

## 修复方向

### 方向 1（置信度: 高）
**重新触发 CI 构建。** 本次失败为 openEuler 官方镜像仓库 `repo.openeuler.org` 的网络瞬态故障（HTTP/2 流错误），与 PR 代码变更无关。在仓库服务恢复后重新运行 CI 即可通过。若多次重试仍失败，需排查 openEuler 镜像仓库 aarch64 节点的 HTTP/2 服务状态。

## 需要进一步确认的点
- 本次构建发生在 `ecs-build-docker-aarch64-04-sp` runner 上，需确认该 runner 与 `repo.openeuler.org` 之间的网络连接是否存在长期问题（如防火墙规则、代理配置等）。
- 需确认 `repo.openeuler.org` 在构建时段（2026-07-09 13:45 UTC 前后）是否存在服务端 HTTP/2 协议层面的已知故障。

## 修复验证要求
无需代码修复。重新触发 CI 构建后观察 `yum install` 步骤是否成功完成即可。若同一 runner 上反复出现同类 Curl error (92)，建议运维排查该节点到 `repo.openeuler.org` 的网络路径。
