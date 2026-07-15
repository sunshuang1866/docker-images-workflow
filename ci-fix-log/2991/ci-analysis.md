# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 包仓库HTTP2协议错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, dnf install, aarch64

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`
- 失败原因: CI 在 aarch64 runner 上执行 `dnf install` 时，`repo.openeuler.org` 镜像站返回 HTTP/2 协议层错误（Curl error 92: INTERNAL_ERROR），多个 RPM 包（git-core、gcc-c++、guile）下载受此影响。其中 `guile` 包在多次重试后仍失败，耗尽所有镜像重试，导致整个安装步骤失败。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 中 `dnf install -y git gcc gcc-c++ make cmake` 命令完全正确，包名有效（dnf 已成功解析依赖列表并开始下载 156 个包）。失败原因为 `repo.openeuler.org` 在该时间段对 aarch64 架构的 HTTP/2 服务不稳定，属于 CI 基础设施/上游镜像站问题。该 Dockerfile 是一个全新的文件，不存在语法或逻辑错误。

## 修复方向

### 方向 1（置信度: 高）
**重试 CI 构建。** 此失败为 `repo.openeuler.org` 镜像站瞬时 HTTP/2 协议异常导致的 `infra-error`，与代码无关。等待上游镜像站恢复后重新触发 CI 流水线（Jenkins rebuild）即可。所有包名、版本号、Dockerfile 语法均无错误。

### 方向 2（置信度: 中）
如果问题持续出现，可在 Dockerfile 的 `dnf install` 命令前添加 `dnf update --nogpgcheck dnf` 或设置 `http2.disable=1` 在 dnf 配置中临时禁用 HTTP/2，降低对镜像站协议实现的依赖。

## 需要进一步确认的点
- 确认 `repo.openeuler.org` 在 aarch64 架构上的 HTTP/2 服务是否已恢复稳定
- 确认该失败是否在 x86_64 runner 上也发生（本日志仅覆盖 aarch64 构建）
- 如问题持续超过 24 小时，向上游镜像站运维团队反馈 HTTP/2 stream INTERNAL_ERROR 问题
