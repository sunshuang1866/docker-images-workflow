# 修复摘要

## 修复的问题
无需代码修改。该 CI 失败为 openEuler 官方仓库 `repo.openeuler.org` 在 aarch64 架构上的 HTTP/2 服务端瞬时故障（HTTP/2 stream INTERNAL_ERROR），属于基础设施问题（infra-error），与 PR 代码变更无关。

## 修改的文件
无。

## 修复逻辑
CI 分析报告认定失败类型为 `infra-error`，根因为 openEuler 24.03-LTS-SP4 官方仓库在 aarch64 CI runner 上下载 RPM 包时返回 HTTP/2 INTERNAL_ERROR，导致 `guile`、`git-core`、`gcc-c++` 等包下载中断。PR 中新增的 Dockerfile 内容正确，`dnf install` 命令语法无误。按照修复原则，infra-error 无需进行任何代码修改，待仓库服务恢复后重新触发 CI 构建即可通过。

## 潜在风险
无。