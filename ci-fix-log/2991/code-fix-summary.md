# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `infra-error`：openEuler 官方仓库 `repo.openeuler.org` 的 HTTP/2 协议层间歇性流错误（Curl error 92），导致部分 RPM 包下载失败。

## 修改的文件
无

## 修复逻辑
分析报告明确判定失败类型为 `infra-error`，根因为 openEuler 仓库 `repo.openeuler.org` 在 aarch64 架构构建时出现 HTTP/2 流传输错误（`HTTP/2 stream was not closed cleanly: INTERNAL_ERROR`），属于基础设施层面的瞬时网络故障，与 PR #2991 的 Dockerfile 及其他变更文件完全无关。Dockerfile 中的 `dnf install -y git gcc gcc-c++ make cmake && dnf clean all` 命令语法正确，无任何代码逻辑问题。

根据修复原则：**若分析报告指出是 `infra-error`，不强行修改代码**。建议触发 CI 重试（re-run）。

## 潜在风险
无