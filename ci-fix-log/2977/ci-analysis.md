# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2传输中断
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, repo.openeuler.org, No more mirrors to try

## 根因分析

### 直接错误
```
#7 556.2 [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer
#7 836.2 [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install ...` 步骤）
- 失败原因: CI 构建节点（aarch64）从 `repo.openeuler.org` 下载 RPM 包时，多次遭遇 HTTP/2 传输层中断（Curl error 92: INTERNAL_ERROR）和 SSL 读取失败（Curl error 56: SSL_ERROR_SYSCALL），最终 `vim-common` 包耗尽了所有镜像尝试次数，yum 安装失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 仅新增了一个 Dockerfile（含 `yum install` 命令）和配套元数据文件。Dockerfile 中的 `yum install` 命令语法正确，包名有效（日志显示 173 个包的依赖解析成功完成并开始下载，且在其中 172 个包已成功下载后，仅 `vim-common` 因网络问题下载失败）。失败纯粹由 `repo.openeuler.org` 镜像站与 CI aarch64 构建节点之间的网络传输不稳定导致，属于基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需代码修复。** 这是 CI 基础设施网络问题，与 PR 代码变更无关。重试 CI 构建即可，网络波动通常是暂时性的。若频繁出现，需由 CI 运维团队排查 `repo.openeuler.org` 对 aarch64 构建节点的 HTTP/2 传输稳定性，或在 yum 仓库配置中添加更多镜像源作为 fallback。

## 需要进一步确认的点
- 该 aarch64 CI 节点到 `repo.openeuler.org` 的网络链路是否长期不稳定（检查近期同节点其他构建是否也有类似 HTTP/2 stream error）
- 是否只有 aarch64 架构节点有此问题（x86_64 构建是否正常完成）
- `repo.openeuler.org` 的 HTTP/2 服务端在构建时段是否存在性能或配置问题
