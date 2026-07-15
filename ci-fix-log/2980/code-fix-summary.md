# 修复摘要

## 修复的问题
CI 构建失败 — openEuler 24.03-LTS-SP4 软件包仓库在下载 `gcc-c++` 包时出现 HTTP/2 流协议错误（Curl error 92），导致 `dnf install` 失败。

## 修改的文件
无代码修改。

## 修复逻辑
失败类型为 **infra-error**，与 PR 代码变更无关。Dockerfile 语法正确，所列软件包均为 openEuler 24.03-LTS-SP4 仓库中实际存在的包（dnf 已成功解析依赖并列出 258 个待安装包）。失败原因是 openEuler 官方仓库在构建时间段内 HTTP/2 传输层不稳定，属于临时基础设施问题。建议**重新触发 CI 构建**，无需修改任何代码。

## 潜在风险
无。