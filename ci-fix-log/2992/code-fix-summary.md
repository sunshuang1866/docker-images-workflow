# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 openEuler 24.03-LTS-SP4 仓库镜像的 HTTP/2 协议层瞬态故障（Curl error 92: Stream error in the HTTP/2 framing layer），与 PR 变更无关。

## 修改的文件
无（infra-error，不需要修改任何源文件）

## 修复逻辑
分析报告明确指出：
- 失败类型为 `infra-error`（CI 基础设施问题）
- 根因是 SP4 仓库镜像服务器 HTTP/2 协议栈异常，导致 `gcc` 等大型 RPM 包下载时 TCP 流异常关闭（`INTERNAL_ERROR`）
- "与 PR 变更无关"——Dockerfile 中的 `dnf install` 命令语法和包名均正确无误
- 推荐修复方向：重新触发 CI 构建即可

## 潜在风险
无