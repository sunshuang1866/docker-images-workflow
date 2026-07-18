# CI 失败分析报告

## 基本信息
- PR: #2991 — chore(vvenc): add openEuler 24.03-LTS-SP4 support
- 失败类型: infra-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: 仓库HTTP/2流错误
- 新模式症状关键词: Curl error (92), HTTP/2 framing layer, INTERNAL_ERROR (err 2), MIRROR, Cannot download, No more mirrors to try

## 根因分析

### 直接错误
```
#7 1273.6 [MIRROR] git-core-2.54.0-2.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/git-core-2.54.0-2.oe2403sp4.aarch64.rpm [HTTP/2 stream 43 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1419.8 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 39 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1548.4 [MIRROR] gcc-c++-12.3.1-110.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 51 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [MIRROR] guile-2.2.7-6.oe2403sp4.aarch64.rpm: Curl error (92): Stream error in the HTTP/2 framing layer for ... [HTTP/2 stream 49 was not closed cleanly: INTERNAL_ERROR (err 2)]
#7 1709.6 [FAILED] guile-2.2.7-6.oe2403sp4.aarch64.rpm: No more mirrors to try - All mirrors were already tried without success
#7 1709.7 Error: Error downloading packages:
#7 ERROR: process "/bin/sh -c dnf install -y git gcc gcc-c++ make cmake && dnf clean all" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6`（`RUN dnf install -y git gcc gcc-c++ make cmake && dnf clean all`）
- 失败原因: aarch64 架构 CI runner 在 Docker 构建过程中，从 `repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/` 下载 RPM 包时，多个包（git-core、gcc-c++、guile）均遭遇 HTTP/2 流层错误（Curl error 92: INTERNAL_ERROR），最终 guile 包耗尽所有镜像源后下载失败，dnf 安装退出码为 1。这是 openEuler 24.03-LTS-SP4 仓库基础设施端（repo.openeuler.org 或中间网络）的 HTTP/2 传输不稳定问题，与 PR 代码变更无关。

### 与 PR 变更的关联
PR 新增了 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile`，其 `dnf install` 指令完全正确——仅安装标准包 `git gcc gcc-c++ make cmake`，语法无任何问题。失败是由 openEuler 24.03-LTS-SP4 官方仓库的 HTTP/2 网络传输故障导致的，与 Dockerfile 内容无关。该 PR 的 README.md、image-info.yml、meta.yml 变更也均为纯元数据更新，不会触发此故障。

## 修复方向

### 方向 1（置信度: 高）
此为 CI 基础设施问题（`repo.openeuler.org` 的 HTTP/2 服务端在 aarch64 构建时段内不稳定），**Code Fixer 无需处理**。建议：
- 等待 openEuler 仓库端网络恢复后重新触发 CI（`retest`）
- 如反复出现，可考虑在 Dockerfile 中为 dnf 配置更多镜像源（如华为云 mirror），或对 `repo.openeuler.org` 强制使用 HTTP/1.1 下载（设置 dnf/curl 的 HTTP 版本协商）

## 需要进一步确认的点
1. x86-64 架构的构建 job 是否也以相同错误失败？当前仅提供了 aarch64 日志，如果 x86-64 也失败且报错相同，说明是仓库端全局问题；如果 x86-64 成功，说明问题仅限于 aarch64 侧特定包或特定时段。
2. `repo.openeuler.org` 当前 HTTP/2 服务状态是否已恢复？可通过手动 curl 测试 `https://repo.openeuler.org/openEuler-24.03-LTS-SP4/OS/aarch64/Packages/` 验证。

## 修复验证要求
无需验证（infra-error，非代码修复类型）。
