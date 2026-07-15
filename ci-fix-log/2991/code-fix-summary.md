# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `infra-error`，由上游仓库 `repo.openeuler.org` 的 HTTP/2 协议层临时性服务端异常（Curl error 92, INTERNAL_ERROR）导致 RPM 包下载失败，与 PR 代码变更完全无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：此次 PR #2991 仅新增了 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据文件，Dockerfile 中第 6 行的 `dnf install -y git gcc gcc-c++ make cmake` 语法和包声明均无问题。失败的直接原因是 `repo.openeuler.org` 镜像站在 CI 运行时段（2026-07-09）对 aarch64 架构的 SP4 仓库出现了 HTTP/2 协议层服务端异常，gcc-c++、git-core、guile 等多个包均遭遇 Curl error (92) —— HTTP/2 传输层流错误（`INTERNAL_ERROR`），所有镜像重试均耗尽后 `guile` 包下载失败导致构建退出。

此为 `infra-error`，属于 CI 基础设施/上游仓库稳定性问题，与 PR 代码变更无关，无需进行代码修改。建议重新触发 CI 构建，待上游仓库恢复后构建应能通过。

## 潜在风险
无