# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 软件源下载中断
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install

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
- 失败原因: aarch64 CI runner 在执行 `yum install` 从 `repo.openeuler.org` 下载 173 个 RPM 依赖包时，`repo.openeuler.org` 服务器端出现间歇性 HTTP/2 连接中断（curl error 92: INTERNAL_ERROR）和 SSL 传输失败（curl error 56: SSL_ERROR_SYSCALL）。虽然 yum 的重试机制使大部分包最终下载成功，但 `vim-common` 包在耗尽了所有 mirror 重试后仍下载失败，导致整个 `yum install` 步骤以 exit code 1 结束。

### 与 PR 变更的关联
**本次失败与 PR 变更无关。** 该 PR 新增的 Dockerfile 内容本身语法正确、依赖声明合理，`yum install` 命令中列出的所有包名（git、gcc、gcc-c++、make、cmake、openssl-devel、gflags-devel、protobuf-devel、protobuf-compiler、abseil-cpp-devel、leveldb-devel、snappy-devel）均为 openEuler 24.03-LTS-SP4 仓库中真实存在的有效包（日志中 yum 已成功解析了全部 173 个包的依赖关系并开始下载）。失败纯粹由 `repo.openeuler.org` 镜像站在该时段的网络不稳定所致。

## 修复方向

### 方向 1（置信度: 高）
**无需修改代码，重试 CI 即可。** 本次失败是 openEuler 官方软件源 `repo.openeuler.org` 在 CI 构建时段的瞬时网络波动导致的 infra-error。日志中多个包（gcc、kernel-headers、perl-MIME-Base64）在首次下载失败后通过 yum 的 mirror 重试机制均下载成功，`vim-common` 是唯一未能在重试上限内成功下载的包。建议触发重新构建，大概率可直接通过。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在该时段是否有服务端异常或维护公告。
- 如果相同 CI runner 节点反复出现此问题，可联系 openEuler 基础设施团队排查 aarch64 runner 到 `repo.openeuler.org` 的网络质量（HTTP/2 连接稳定性）。
