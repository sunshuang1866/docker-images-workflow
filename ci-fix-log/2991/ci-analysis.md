# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 包仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), Stream error in the HTTP/2 framing layer, INTERNAL_ERROR, repo.openeuler.org, dnf download

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/gcc-c%2b%2b-12.3.1-110.oe2403sp4.aarch64.rpm [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/guile-2.2.7-6.oe2403sp4.aarch64.rpm [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 1709.7   guile-5:2.2.7-6.oe2403sp4.aarch64: Cannot download, all mirrors were already tried without success
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:6 (`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`)
- 失败原因: `repo.openeuler.org` 的 openEuler-24.03-LTS-SP4 OS 仓库（aarch64 架构）在提供 HTTP/2 下载服务时频繁返回 `INTERNAL_ERROR`（err 2），导致 dnf 在尝试所有镜像源后仍无法下载 `guile-5:2.2.7-6.oe2403sp4.aarch64` 包（`git` 的传递依赖），构建失败。

### 与 PR 变更的关联
**与 PR 变更无关。** 本次 PR 仅新增了一个标准的 Dockerfile，其 `dnf install` 命令语法正确、依赖声明完整。失败根因是 `repo.openeuler.org` 的 aarch64 仓库（OS 子仓库）在构建时间段内存在 HTTP/2 协议层面的服务端错误，属于纯基础设施问题。多个包（`git-core`、`gcc-c++`、`guile`）在不同 HTTP/2 流上均遭遇相同错误，排除了单个文件损坏的可能性。

## 修复方向

### 方向 1（置信度: 中）
重试构建。这是 `repo.openeuler.org` 的 aarch64 OS 仓库 HTTP/2 服务端瞬时故障，通常重试即可成功。可等待基础设施团队修复后重新触发 CI。

### 方向 2（置信度: 低）
在 Dockerfile 的 `dnf install` 前强制 dnf/libcurl 使用 HTTP/1.1，绕过 HTTP/2 层的问题：
- 通过 `RUN echo "http2=false" >> /etc/dnf/dnf.conf` 或环境变量禁用 HTTP/2
- 但这仅是客户端 workaround，不应作为长期方案，根本修复需由 repo.openeuler.org 运维团队排查 HTTP/2 服务端内部错误。

## 需要进一步确认的点
- `repo.openeuler.org` 的 aarch64 OS 仓库 HTTP/2 服务是否已恢复正常（可联系基础设施团队确认）。
- 同一时间段内其他使用 `openEuler-24.03-LTS-SP4` 基础镜像的 aarch64 构建是否也遭遇相同问题（如存在，说明是仓库级故障而非本 PR 个例）。
- x86_64 架构的 vvenc 构建是否成功（本次日志仅包含 aarch64 runner 的输出）。

## 修复验证要求
无需 code-fixer 验证。本失败为 infra-error，非代码问题，Code Fixer 无需处理。
