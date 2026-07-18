# 修复摘要

## 修复的问题
无需代码修改。CI 失败原因为 openEuler 24.03-LTS-SP4 仓库（`repo.****.org`）在构建时刻出现 HTTP/2 流错误（Curl error 92: Stream error in the HTTP/2 framing layer），导致 dnf 下载 RPM 包失败。此为基础设施网络问题（infra-error），与 PR #2992 的代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出本次失败为 infra-error，失败的直接原因是 CI 构建环境在从 openEuler 24.03-LTS-SP4 仓库下载 RPM 包时遭遇 HTTP/2 协议层面的连接异常。Dockerfile 内容正确（基础镜像、dnf 包列表、编译步骤、多阶段构建均无语法或逻辑错误），无需修改任何代码文件。建议在构建环境网络恢复正常后重新触发 CI 流水线（re-run / retry）。

## 潜在风险
无