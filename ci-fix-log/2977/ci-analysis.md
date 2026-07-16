# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP2传输中断
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, yum install, repo.openeuler.org

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
- 失败原因: 构建过程中 `repo.openeuler.org` 镜像站对 aarch64 架构 RPM 包的 HTTP/2 传输持续出现流中断（curl error 92 INTERNAL_ERROR）和 SSL 读取失败（curl error 56 SSL_ERROR_SYSCALL），多个包（gcc、kernel-headers、perl-MIME-Base64）经 yum 内置重试后成功，但最后一个包 `vim-common` 重试耗尽后仍未成功，导致 `yum install` 步骤以 exit code 1 终止。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile、README 条目、image-info.yml 条目和 meta.yml 条目，Dockerfile 中的 `yum install` 命令语法和包名均为标准写法。失败纯粹由 `repo.openeuler.org` 镜像站在构建时间窗口内对 aarch64 仓库的 HTTP/2 服务不稳定所致，属于 CI 基础设施层面问题。

## 修复方向

### 方向 1（置信度: 高）
这是 CI 基础设施故障（`infra-error`），与 PR 代码变更无关。Code Fixer 无需对 Dockerfile 或任何代码文件做任何修改。建议：
- **直接重新触发 CI 构建**（retrigger the pipeline），在镜像站服务恢复稳定后构建大概率成功。
- 若反复出现同类问题，可由 CI 管理员评估是否为 `repo.openeuler.org` 添加备用镜像源或为 `yum install` 添加 `--retries` 参数。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 aarch64 仓库在构建时是否确实存在服务端 HTTP/2 流不稳定问题（可通过在 CI runner 上手动 `curl` 测试验证）。
- 确认同类失败是否为偶发（单次网络抖动）还是持续性问题（需要仓库运维介入）。

## 修复验证要求
- 无需修复。重新触发 CI 构建即可。若重新构建后仍然失败，需获取新的日志进一步分析。
