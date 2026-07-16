# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2下载波动
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, repo.openeuler.org

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer ... [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer ...
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install` 步骤）
- 失败原因: 在 aarch64 runner 上构建时，`repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 仓库 HTTP/2 连接不稳定，多个 aarch64 RPM 包下载出现 Curl error (92) HTTP/2 帧层错误和 Curl error (56) SSL 读错误，其中 `vim-common` 在耗尽所有重试镜像后仍下载失败，导致 `yum install` 命令以 exit code 1 终止。

### 与 PR 变更的关联
**无关联**。PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件（README.md、image-info.yml、meta.yml），Dockerfile 中 `yum install` 的包列表和写法均属标准操作。失败根因是 CI 构建期间 `repo.openeuler.org` 仓库的 HTTP/2 传输层出现间歇性错误，与 PR 代码变更完全无关。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建**。该失败为 openEuler 官方软件仓库 `repo.openeuler.org` 在构建时段的临时性 HTTP/2 协议层不稳定所致（4 个不同包先后出现 Curl 92/56 错误），与代码无关。等待仓库恢复稳定后重新触发 CI 构建即可。

### 方向 2（置信度: 低）
**在 Dockerfile 中为 yum 添加重试机制**。若此问题频繁复现，可在 `yum install` 前配置 `retries` 和 `timeout` 参数（如 `echo "retries=10" >> /etc/yum.conf`），但这属于规避方案而非根因修复，且对 HTTP/2 帧层错误的效果有限。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段（2026-07-09 13:45 UTC）是否存在已知的网络或服务异常。
- 确认其他 openEuler 24.03-LTS-SP4 镜像的 CI 构建在相近时段是否也出现同类下载失败，以判断是否为系统性问题。
