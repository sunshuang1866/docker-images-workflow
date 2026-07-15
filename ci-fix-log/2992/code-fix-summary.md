# 修复摘要

## 修复的问题
CI 基础设施故障：openEuler 24.03-LTS-SP4 RPM 仓库在构建期间出现 HTTP/2 流错误（Curl error 92），导致 `dnf install` 下载 RPM 包失败。此问题与 PR 代码变更无关。

## 修改的文件
无。此失败为 `infra-error`，无需对任何源代码文件进行修改。

## 修复逻辑
根据 CI 失败分析报告，失败的根因是 openEuler 24.03-LTS-SP4 官方 RPM 仓库侧的网络/服务端 HTTP/2 协议异常（`INTERNAL_ERROR (err 2)`），属于临时性基础设施问题。PR 中新增的 Dockerfile（`Others/multiwfn/cb37c53/24.03-lts-sp4/Dockerfile`）语法正确、包声明无误。两个构建阶段（builder 和最终阶段）在下载不同 RPM 包集合时均遭遇同一类错误，进一步佐证问题出在上游仓库而非代码。修复方向为触发 CI 重试，待仓库服务恢复稳定后构建即可通过。

## 潜在风险
无。无代码变更，不引入任何风险。