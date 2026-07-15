# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 上游仓库下载网络异常
- 新模式症状关键词: Curl error, HTTP/2, repo.openeuler.org, yum install, aarch64, No more mirrors to try, INTERNAL_ERROR

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
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4`（`RUN yum install` 步骤）
- 失败原因: 在 aarch64 构建节点（`ecs-build-docker-aarch64-04-sp`）上，`yum install` 从 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 下载 RPM 包时，多次遭遇 HTTP/2 协议层错误（Curl error 92: INTERNAL_ERROR）和 SSL 连接重置（Curl error 56），最终 `vim-common` 包耗尽所有镜像源重试后仍下载失败，导致整个 yum 事务中断。

### 与 PR 变更的关联
**与 PR 代码变更无关**。PR 仅新增了一个正确的 Dockerfile（及配套元数据文件），`yum install` 命令语法、包名均无误（日志中 Transaction Summary 显示所有 173 个包均被正确解析）。失败是由于 openEuler 24.03-LTS-SP4 的 aarch64 官方仓库 `repo.openeuler.org` 在构建期间出现间歇性网络不稳定，部分 RPM 包的 HTTP/2 传输被异常中断。属于 CI 基础设施/上游服务问题。

## 修复方向

### 方向 1（置信度: 高）
**重试构建**。这是上游 `repo.openeuler.org` aarch64 仓库的瞬时网络故障，PR 代码无任何问题。等待上游仓库恢复稳定后重新触发 CI 构建即可。如果问题持续复现，建议联系 openEuler 基础设施团队排查 `repo.openeuler.org` 的 aarch64 SP4 仓库服务端 HTTP/2 配置或负载均衡器问题。

### 方向 2（置信度: 低）
在 Dockerfile 的 `yum install` 命令中添加 `--retries 10 --retry-delay 30` 等重试参数以增强对上游仓库间歇性网络波动的容错能力。但这属于规避而非修复根因，且 yum 本身已有 mirror 重试机制（日志中显示已尝试所有 mirror），效果有限。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在当前时间点是否已恢复稳定（可在非 CI 环境手动执行 `yum install vim-common` 验证）
- 如果该问题在多次重试后仍持续出现，需要在 openEuler 基础设施侧排查 CDN/负载均衡节点的 HTTP/2 协议实现是否存在 bug
- 检查是否有其他同日构建的 SP4 aarch64 镜像也遭遇相同网络错误，以确认是否为仓库侧的普遍性问题而非单次偶发
