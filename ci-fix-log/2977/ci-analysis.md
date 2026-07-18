# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库源网络抖动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

前序同类错误（非致命，但表明网络持续不稳定）：
```
#7 556.2  [MIRROR] gcc-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 41 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 836.2  [MIRROR] kernel-headers-6.6.0-159.4.3.154.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer [HTTP/2 stream 59 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1029.3 [MIRROR] perl-MIME-Base64-3.16-2.oe2403sp4.aarch64.rpm: Curl error (56): Failure when receiving data from the peer [OpenSSL SSL_read: SSL_ERROR_SYSCALL, errno 0]
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`yum install` 步骤）
- 失败原因: 在 aarch64 runner 上执行 `yum install` 时，`repo.openeuler.org` 仓库源持续出现 HTTP/2 流错误（Curl error 92）和 SSL 读取失败（Curl error 56），多次重试后 `vim-common` 包下载耗尽所有镜像源（No more mirrors to try），导致 yum 安装失败。

### 与 PR 变更的关联
**与 PR 代码变更无关。** PR 新增的 Dockerfile 在语法和包名选择上均正确——yum 在"Transaction Summary"阶段成功识别了全部 173 个待安装包（包括 gcc、kernel-headers、vim-common 等），说明这些包在 openEuler 24.03-LTS-SP4 仓库中确实存在。失败纯粹由构建环境到 `repo.openeuler.org` 的网络不稳定导致，属于 CI 基础设施问题。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 Dockerfile 代码。** 这是 CI 基础设施的瞬时网络故障（`repo.openeuler.org` 在构建期间 HTTP/2 连接不稳定）。Code Fixer 无需处理此 PR，等待 CI 基础设施网络恢复后重新触发构建即可。

### 方向 2（可选，置信度: 中）
若该问题频繁复现，可考虑在 Dockerfile 的 `yum install` 命令前添加 yum 重试/超时配置（如 `echo "retries=10" >> /etc/yum.conf` 或 `echo "timeout=300" >> /etc/yum.conf`）以增强对网络波动的容忍度。但这属于优化措施，非本次 PR 的必修复项。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在构建时段是否存在已知的服务降级或维护。
- 若多次重试 CI 后仍然失败，需排查 CI runner 节点（`ecs-build-docker-aarch64-04-sp`）到 `repo.openeuler.org` 的网络路由是否稳定。
