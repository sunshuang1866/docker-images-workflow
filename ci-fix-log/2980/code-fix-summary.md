# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 openEuler 24.03-LTS-SP4 官方软件仓库在构建时刻的 HTTP/2 传输层瞬态故障（Curl error 92），属于基础设施错误（infra-error），与 PR 代码变更无关。

## 修改的文件
无。未修改任何文件。

## 修复逻辑
CI 分析报告明确指出：该失败为纯基础设施/网络层故障。多个 RPM 包（`cmake-data`、`git-core`、`gcc-c++`）在下载过程中出现 `HTTP/2 stream INTERNAL_ERROR`，前两个包在重试后成功，`gcc-c++` 两次重试后失败。PR 新增的 Dockerfile 中 `dnf install` 命令语法正确、依赖包列表完整，无需任何代码修改。建议重新触发 CI 构建，镜像仓库恢复后应能通过。

## 潜在风险
无。未修改任何代码。