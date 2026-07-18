# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: YUM镜像源下载故障
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: openEuler 官方镜像站 `repo.openeuler.org` 的 HTTP/2 传输层存在不稳定问题，多个 aarch64 架构 RPM 包下载过程中遭遇 HTTP/2 帧错误（INTERNAL_ERROR）和 SSL 读取失败（SSL_ERROR_SYSCALL），部分包（gcc、kernel-headers）经重试其他镜像后成功，但 vim-common 最终耗尽所有镜像仍下载失败，导致 yum install 以 exit code 1 退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及相关元数据（README.md、image-info.yml、meta.yml），Dockerfile 中的 `yum install` 包列表均为 openEuler 24.03-LTS-SP4 仓库中的合法包名。CI 构建在 aarch64 节点上执行时，`repo.openeuler.org` 镜像站的 HTTP/2 服务出现间歇性故障，导致 RPM 包下载失败。这是一个纯基础设施网络问题，与代码变更无关。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重新触发 CI 构建即可。** 该失败是由 openEuler 镜像站在该时间窗口内的 HTTP/2 服务不稳定导致的瞬态网络错误，与 PR 代码变更无关。在镜像站服务恢复正常后重新运行 CI job 应能通过。若反复出现同类问题，建议在 Dockerfile 的 `yum install` 命令中添加重试参数（如 `--retries=3`）或在 CI 层面配置构建失败自动重试。

## 需要进一步确认的点
- 检查同一 PR 的 x86-64 (amd64) 架构构建 job 是否也失败，如果 amd64 通过而 aarch64 失败，则进一步证明是 aarch64 镜像站节点的局部网络问题。
- 确认 `repo.openeuler.org` 在该时间段是否有已知的服务中断或维护公告。
