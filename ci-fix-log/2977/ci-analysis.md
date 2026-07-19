# CI 失败分析报告

## 基本信息
- PR: #2977 — chore(brpc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 镜像站HTTP/2网络波动
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR, Curl error (56), SSL_ERROR_SYSCALL, No more mirrors to try, yum install

## 根因分析

### 直接错误
```
#7 1310.2 [MIRROR] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm [HTTP/2 stream 125 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1310.2 [FAILED] vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1310.3 Error: Error downloading packages:
#7 1310.3   vim-common-2:9.0.2092-36.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c yum install -y ..." did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/brpc/1.16.0/24.03-lts-sp4/Dockerfile:4-11`（`RUN yum install -y` 步骤）
- 失败原因: CI 在 aarch64 runner 上构建时，`repo.openeuler.org` 镜像站的 openEuler 24.03-LTS-SP4 aarch64 仓库出现 HTTP/2 连接异常（Curl error 92: INTERNAL_ERROR）和 SSL 读取错误（Curl error 56: SSL_ERROR_SYSCALL），导致多个 RPM 包下载失败。yum 自动重试机制解决了 `gcc`、`kernel-headers`、`perl-MIME-Base64` 的失败下载，但 `vim-common`（7.8 MB）耗尽所有重试后仍失败，yum 安装中断并返回 exit code 1。

### 与 PR 变更的关联
**与 PR 代码无关。** PR 仅新增了一个 brpc 1.16.0 的 Dockerfile，其 `yum install` 命令中列出的包均为正常可用的开发依赖，不存在语法错误或错误的包名。失败完全由 `repo.openeuler.org` 镜像站的网络基础设施问题导致（aarch64 架构 SP4 仓库的 HTTP/2 连接不稳定）。该构建如果重新触发，在网络正常时可成功完成。

## 修复方向

### 方向 1（置信度: 高）
**无需修改 PR 代码，重新触发 CI 构建即可。** 这是镜像站临时性网络波动问题，非代码缺陷。若问题持续复现，考虑：
- 在 `yum install` 前添加 `yum makecache` 预热仓库元数据，或添加 `--retries` 相关参数增加重试次数
- 向 openEuler 基础设施团队反馈 `repo.openeuler.org` 的 SP4 aarch64 仓库 HTTP/2 服务稳定性问题

## 需要进一步确认的点
- 如果多次重试 CI 仍然失败，需要确认 `repo.openeuler.org` 的 SP4 aarch64 仓库是否存在持续的服务端问题，或 CI runner 到该镜像站的网络链路是否稳定
- 可尝试在相同时间点手动 `curl` 测试 `https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/vim-common-9.0.2092-36.oe2403sp4.aarch64.rpm` 的连通性
