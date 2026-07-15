# 修复摘要

## 修复的问题
CI 基础设施问题（openEuler 24.03-LTS-SP4 RPM 仓库镜像 HTTP/2 流错误），无需代码修改。

## 修改的文件
无（infra-error，与 PR 代码变更无关）

## 修复逻辑
分析报告明确指出此次失败为 `infra-error`，根因是 CI 构建环境在从 openEuler 仓库镜像下载 RPM 包时遭遇 HTTP/2 传输层错误（Curl error 92），`gcc-c++` 等包在多次重试后仍下载失败。PR 新增的 Dockerfile 语法正确，`dnf install` 命令参数和包名均无问题，失败与 PR 变更无关。

建议操作：在 PR 上重新触发 CI 构建，该问题大概率不会复现。

## 潜在风险
无