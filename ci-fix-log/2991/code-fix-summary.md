# 修复摘要

## 修复的问题
无需代码修复。CI 失败是由于 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库在构建时出现 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），属于临时性基础设施故障，与 PR 代码无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出失败类型为 `infra-error`，根因是 `repo.openeuler.org` 服务端 HTTP/2 协议层瞬时故障，导致 `dnf install` 过程中 `gcc-c++`、`git-core`、`guile` 三个 RPM 包下载失败。PR 仅新增了 vvenc 1.14.0 在 openEuler 24.03-lts-sp4 上的 Dockerfile 及配套元数据，代码逻辑无缺陷。建议重新触发 CI 构建，仓库恢复后相同代码应能通过。

## 潜在风险
无