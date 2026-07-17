# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 openEuler 24.03-LTS-SP4 官方软件仓库的瞬时 HTTP/2 传输故障（Curl error 92: Stream error in the HTTP/2 framing layer）引起，属于基础设施问题（infra-error），与 PR 新增的 Dockerfile 配置无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：
- 失败类型为 `infra-error`，置信度高
- 失败原因是 openEuler `repo.****.org` 仓库在构建期间（2026-07-09 14:46~14:47 UTC）出现 HTTP/2 协议传输故障，多个 RPM 包下载时遭遇 `Curl error (92): INTERNAL_ERROR`
- Dockerfile 中 `dnf install` 命令语法正确，包名均为合法包
- 与 PR 变更无关联

修复方向为：**重试 CI**（如 `/retest` 或重新 push）。等待仓库恢复后重新触发构建即可。

## 潜在风险
如果多次重试后仍出现相同的 HTTP/2 流错误，则需考虑在 Dockerfile 中为 `dnf` 配置 `http2=false` 或切换到 HTTP/1.1 连接。