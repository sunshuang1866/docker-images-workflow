# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库镜像网络波动
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install, repo.openeuler.org

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
- 失败原因: CI 构建节点（`ecs-build-docker-aarch64-04-sp`）在 aarch64 架构上执行 yum 安装依赖包时，`repo.openeuler.org` 仓库镜像出现间歇性网络故障——多个大型 RPM 包（gcc、kernel-headers、vim-common）遭遇 HTTP/2 流错误（Curl error 92）和 SSL 读取失败（Curl error 56），最终 `vim-common` 包因所有镜像均尝试失败而无法下载，导致整个 `yum install` 步骤以 exit code 1 失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 此次 PR 的改动为：
1. 新增 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`（25 行，构建 brpc 1.16.0 镜像）
2. 更新 `Others/brpc/README.md`（添加新 Tag 行）
3. 更新 `Others/brpc/doc/image-info.yml`（添加新 Tag 行）
4. 更新 `Others/brpc/meta.yml`（添加 `1.16.0-oe2403sp4` 条目）

失败发生在 Docker 构建的最早阶段——第一步 `yum install` 从 openEuler 官方仓库下载依赖包时，属于纯粹的 CI 基础设施网络问题。Dockerfile 本身的 `yum install` 命令语法、包名配置均无错误（日志中 `Dependencies resolved` 阶段显示 173 个包均被正确识别）。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 该失败为 openEuler 24.03-LTS-SP4 仓库镜像的临时网络波动（HTTP/2 流错误 + SSL 读取失败），与 PR 代码变更完全无关。等待仓库镜像恢复后重新触发 CI 构建即可通过。无需修改 Dockerfile 或任何代码。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 aarch64 仓库镜像当前是否已恢复正常。可在 CI 构建节点上手动执行 `curl -I https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 验证连通性。
- 如果同一镜像仓库在短时间内多次出现类似网络波动，建议向 openEuler 基础设施团队报告 CDN/镜像站稳定性问题。
- 确认 amd64 架构的构建是否正常通过（当前日志仅来自 aarch64 runner）。如果 amd64 构建正常，则进一步确认问题仅限于 aarch64 仓库镜像节点。
