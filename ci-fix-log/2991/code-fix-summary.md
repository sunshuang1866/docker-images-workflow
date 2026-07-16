# 修复摘要

## 修复的问题
无需代码修复。失败类型为 infra-error，根因是 `repo.openeuler.org` 开源社区仓库在构建时段 HTTP/2 服务端不稳定（Curl error 92: INTERNAL_ERROR），导致 `dnf install` 下载 `guile` 包失败。与本次 PR 的 Dockerfile 代码变更无关。

## 修改的文件
无。此错误非代码问题，属于 CI 基础设施/外部仓库服务不稳定。

## 修复逻辑
分析报告结论：CI 构建在 aarch64 节点上执行 `dnf install` 时，openEuler 官方仓库 `repo.openeuler.org` 的 HTTP/2 连接频繁被服务端以 `INTERNAL_ERROR` 异常关闭，导致 `guile` 包耗尽所有重试次数后彻底失败。Dockerfile 中的 `dnf install` 命令语法正确，失败发生在 Docker 构建的第一个 RUN 层，尚未进入 vvenc 源码编译步骤。同级 PR 的 aarch64 构建若有类似错误可进一步确认是仓库端问题。

**推荐操作**：重新触发 CI 构建。

## 潜在风险
无