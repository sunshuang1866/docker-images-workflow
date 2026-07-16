# 修复摘要

## 修复的问题
CI 失败为基础设施问题（infra-error），无需代码修改。

## 修改的文件
无。CI 失败根因是 `repo.openeuler.org` 的 openEuler 24.03-LTS-SP4 aarch64 仓库存在 HTTP/2 流错误（Curl error 92: Stream error in the HTTP/2 framing layer ... INTERNAL_ERROR），属于仓库服务端基础设施间歇性故障，与 PR 代码变更无关。

## 修复逻辑
根据 CI 失败分析报告的结论，此次失败的根因为 `infra-error`，置信度"高"。Dockerfile 中的 `dnf install` 命令语法正确、依赖声明合理。失败发生在 aarch64 镜像仓库的 HTTP/2 传输层面，即使回退 PR 代码，同一 runner 在同一时刻仍会触发相同错误。按照修复原则，对于 infra-error 类问题不应强行修改代码。

## 潜在风险
无。建议等待 openEuler 镜像仓库 HTTP/2 服务恢复后重试构建。