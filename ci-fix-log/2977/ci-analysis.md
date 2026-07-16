# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: openEuler仓库下载故障
- 新模式症状关键词: Curl error (92), Curl error (56), HTTP/2 stream, No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（yum install 步骤）
- 失败原因: openEuler 24.03-LTS-SP4 官方仓库 `repo.openeuler.org` 在 CI 构建期间出现网络不稳定，多个 RPM 包（gcc、kernel-headers、perl-MIME-Base64、vim-common）下载时遭遇 HTTP/2 流错误（Curl error 92）和 SSL 读取错误（Curl error 56）。前三个包经 yum 自动重试后成功下载，但 `vim-common` 在历经 36 秒后仍无法完成下载，yum 耗尽所有镜像重试后构建失败。

### 与 PR 变更的关联
**与 PR 无关。** 本次 PR 仅新增了一个合法 Dockerfile 和配套元数据文件：
- `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile`（25 行，语法和包名均正确）
- `Others/brpc/README.md`（新增一行表格条目）
- `Others/brpc/doc/image-info.yml`（新增一行条目）
- `Others/brpc/meta.yml`（新增一个 tag 映射）

Dockerfile 中 `yum install` 列出的所有包名均为 openEuler 24.03-LTS-SP4 仓库中的标准软件包，构建失败完全由 `repo.openeuler.org` 的网络抖动导致，在 aarch64 runner `ecs-build-docker-aarch64-04-sp` 上发生。

## 修复方向

### 方向 1（置信度: 高）
**无需修复代码，重新触发 CI 构建即可。** 此次失败是 `repo.openeuler.org` 仓库的瞬时网络故障（HTTP/2 流中断），属于基础设施问题。172 个 RPM 包中有 168 个成功下载，仅 `vim-common` 因连续网络错误耗尽重试次数。重新运行 CI pipeline 大概率可以通过。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在重新构建时网络已恢复正常。若多次重试均以相同模式失败，则需排查 openEuler 24.03-LTS-SP4 aarch64 仓库侧是否存在持续的 CDN/负载均衡问题。
