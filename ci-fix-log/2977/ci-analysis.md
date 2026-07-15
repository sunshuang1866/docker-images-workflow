# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库包下载网络故障
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, MIRROR, No more mirrors to try, yum

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
- 失败原因: CI aarch64 runner 在 Docker 构建过程中从 `repo.openeuler.org` 下载 173 个 RPM 包时，多个包（gcc、kernel-headers、perl-MIME-Base64、vim-common）遇到 HTTP/2 传输层错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接中断（Curl error 56）。yum 的重试机制让前三个包最终下载成功，但 `vim-common`（7.8MB）在重试耗尽后仍未成功，最终导致 yum 安装步骤失败。172/173 个包已成功下载。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 的变更内容为：
1. 新增 `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`（完整的 brpc 编译镜像构建文件）
2. 更新 `Others/brpc/README.md`、`Others/brpc/doc/image-info.yml`、`Others/brpc/meta.yml`（描述新镜像的元数据）

Dockerfile 本身语法正确、包名合理，`yum install` 的命令格式也无误。构建失败纯粹是因为 CI runner 与 `repo.openeuler.org` 之间的网络不稳定，导致部分 RPM 包下载失败。该问题同样可能影响其他使用同版本基础镜像的构建。

## 修复方向

### 方向 1（置信度: 高）
**重试构建。** 这是一个基础设施/网络稳定性问题，与 Dockerfile 内容无关。网络环境恢复后重新触发 CI 构建即可通过。

### 方向 2（置信度: 中）
**在 yum 配置中启用 retries 和 timeout 优化。** 如果该网络问题在 aarch64 runner 上频繁复现，可在 Dockerfile 中为 yum 添加重试和超时参数（如 `yum install -y --setopt=retries=10 ...`），增强对临时网络波动的容忍度。但这不是根本解决方案——根本原因在于 CI 基础设施的网络稳定性。

## 需要进一步确认的点
1. `repo.openeuler.org` 在该时间段是否有已知的服务降级或维护事件。
2. 同一时间段内 aarch64 架构其他镜像的构建是否也出现了类似网络错误——如果是，则确认是仓库侧问题而非 runner 个体问题。
3. gcc（30MB）、kernel-headers（1.7MB）、perl-MIME-Base64（19KB）、vim-common（7.8MB）这 4 个包出错的包大小跨度很大（从 19KB 到 30MB），排除"大文件传输不兼容"的可能性，更指向随机性网络抖动。
4. `Finished: FAILURE` 仅出现在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上，需确认 x86_64 runner 是否也有相同问题（如 x86_64 通过，则可判定为 aarch64 runner 所在网络环境或 aarch64 仓库 CDN 节点问题）。
