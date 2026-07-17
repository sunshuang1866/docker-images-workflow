# 修复摘要

## 修复的问题
本次 CI 失败为 `infra-error`，由 openEuler 官方仓库 `repo.openeuler.org` 在 aarch64 构建期间的 HTTP/2 传输层瞬时故障引起（Curl error 92: HTTP/2 stream INTERNAL_ERROR），与 PR 代码变更无关。无需对任何源文件进行代码修改。

## 修改的文件
无代码修改。

## 修复逻辑
CI 失败分析报告明确指出：
- 失败发生在 `Others/vvenc/1.14.0/24.03-lts-sp4/Dockerfile:6` 的 `dnf install` 阶段
- 根因为 `repo.openeuler.org` 仓库在构建时段向 aarch64 节点提供 RPM 包时发生 HTTP/2 流错误，导致多个包下载中断
- PR 的 `dnf install` 命令语法正确、依赖声明合理，**与 PR 代码变更完全无关**

修复方向为重新触发 CI 构建，等待仓库服务恢复稳定后重试即可通过。

## 潜在风险
无。