# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: yum仓库网络错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, MIRROR, No more mirrors to try, repo.openeuler.org, aarch64

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
#7 ERROR: process "/bin/sh -c yum install -y ... && yum clean all && rm -rf /var/cache/yum" did not complete successfully: exit code: 1
------Dockerfile:4
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install -y ...` 步骤）
- 失败原因: CI 在 aarch64 runner（`ecs-build-docker-aarch64-04-sp`）上通过 `yum` 从 `repo.openeuler.org` 下载 173 个 RPM 包时，多个包遭遇 HTTP/2 协议层错误（curl error 92: `INTERNAL_ERROR`）和 SSL 连接中断（curl error 56: `SSL_ERROR_SYSCALL`）。前 3 个受影响包（gcc、kernel-headers、perl-MIME-Base64）经重试后下载成功，但第 4 个受影响包 `vim-common` 在重试所有镜像后仍失败，导致整个 `RUN` 命令以 exit code 1 退出。

### 与 PR 变更的关联
**此失败与 PR 代码变更无关。** PR 仅新增了一个标准的 Dockerfile，其中 `yum install` 命令列出的依赖包名称均正确且对应 `oe2403sp4` 版本。yum 仓库元数据解析正常（成功确定 173 个待安装包及依赖关系），下载过程中 `repo.openeuler.org` 出现 HTTP/2 协议层异常属于 CI 运行时基础设施的瞬时网络问题，非 Dockerfile 配置或包名错误。日志中 gcc 和 kernel-headers 包也曾报告同样的 curl error 92 但重试成功，进一步说明这是远程服务器的间歇性故障。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，重新触发 CI 构建即可。** 该失败为 openEuler 官方仓库 `repo.openeuler.org` 在 aarch64 runner 上的瞬时网络/协议层故障（HTTP/2 stream INTERNAL_ERROR、SSL read 中断）。前 3 个遭遇同类错误的包均通过重试成功下载，说明 yum 自带的镜像重试机制可覆盖多数情况，而 `vim-common` 因重试次数耗尽而最终失败。在仓库服务恢复稳定后重新运行 CI 有较高概率通过。

### 方向 2（置信度: 低）
如果反复重试仍失败，可能 `repo.openeuler.org` 对 aarch64 架构的某个镜像存在持续性问题。此时可考虑在 Dockerfile 的 `yum install` 前添加 `yum config-manager` 或 `sed` 操作将仓库 URL 换为备用镜像站，但此方向需要先确认仓库问题是否持续存在。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 aarch64 架构上的仓库服务当前状态是否稳定（可通过其他同期 aarch64 CI 构建结果交叉验证）
- 确认该 PR 在 x86_64 runner 上的构建是否正常（日志仅包含 aarch64 runner 的构建过程）
- 如多次重试后 aarch64 构建仍失败，需排查是否是 `vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 这个特定包在镜像站上存在问题（如文件损坏），可对比该包的 SHA256 与实际仓库元数据
