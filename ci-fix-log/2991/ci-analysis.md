# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: dnf仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, repo.openeuler.org, aarch64, dnf install

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
- 失败原因: openEuler 24.03-LTS-SP4 的 aarch64 软件仓库 `repo.openeuler.org` 在下载 RPM 包时频繁出现 HTTP/2 Stream Error (Curl error 92)，其中 `git-core`、`gcc-c++` 重试后恢复，但 `guile` 包耗尽所有镜像重试次数后彻底失败，导致 `dnf install` 退出。

### 与 PR 变更的关联
**与 PR 变更无关。** PR 新增的 Dockerfile 语法正确，`dnf install` 安装的 5 个包（git、gcc、gcc-c++、make、cmake）均为 openEuler 24.03-LTS-SP4 仓库中存在的标准包（dnf 已成功解析依赖和事务摘要）。失败原因是下游软件仓库基础设施问题——repo.openeuler.org 的 aarch64 镜像在 HTTP/2 协议层间歇性出现 `INTERNAL_ERROR` 流重置，属于服务端侧的网络传输问题。该镜像构建在 x86_64 架构上可能正常（日志未覆盖），仅在 aarch64 runner `ecs-build-docker-aarch64-04-sp` 上触发。

## 修复方向

### 方向 1（置信度: 低）
本次失败为 CI 基础设施（openEuler 24.03-LTS-SP4 软件仓库 aarch64 镜像 HTTP/2 服务不稳定）导致的偶发性问题，**Code Fixer 无需介入代码修改**。建议通过以下 CI 运维手段处理：

1. **重试构建**：直接重新触发 CI 流水线，等待仓库服务恢复后通常可通过。
2. **降级 HTTP 协议**（如需增强健壮性）：在 `dnf install` 之前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 或设置 `echo "http2=false" >> /etc/yum.repos.d/*.repo`，强制 dnf/curl 使用 HTTP/1.1 避免 HTTP/2 流错误。但此修改属于规避方案而非根因修复，不在本次分析推荐的修复范围内。

## 需要进一步确认的点
1. 需要检查 openEuler 24.03-LTS-SP4 aarch64 仓库 `repo.openeuler.org` 的当前服务状态，确认 HTTP/2 流错误是否为临时故障还是持续性退化。
2. 需要确认 x86_64 架构的同 PR 构建是否成功（当前日志仅有 aarch64 构建记录），若 x86_64 也失败则问题范围可能更大。
3. 如果未来同仓库其他 PR 也频繁出现此错误，应考虑向 openEuler 基础设施团队报告 `repo.openeuler.org` 的 HTTP/2 服务稳定性问题。
