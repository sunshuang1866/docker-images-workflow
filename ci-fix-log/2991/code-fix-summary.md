# 修复摘要

## 修复的问题
CI 基础设施故障（infra-error），无需修改任何 PR 代码。

## 修改的文件
- 无

## 修复逻辑
CI 失败分析报告确认本次失败为 **infra-error**，与 PR #2991 的代码变更无关。失败原因是 CI 构建节点（aarch64）通过 dnf 从 `repo.openeuler.org` 下载 RPM 包时，HTTP/2 连接多次出现 `INTERNAL_ERROR (err 2)` 流错误，属于 openEuler 仓库服务器的网络瞬时故障。PR 中的 Dockerfile 语法和包列表均正确无误，不需要任何代码修改。直接重新触发 CI 构建（re-run/retry）即可。

## 潜在风险
无