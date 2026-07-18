# 修复摘要

## 修复的问题
无需代码修复。CI 失败为基础设施问题（infra-error），与 PR #2980 代码变更无关。

## 修改的文件
无（infra-error，无需修改任何代码文件）

## 修复逻辑
CI 失败根因是 openEuler 24.03-LTS-SP4 RPM 仓库的 HTTP/2 协议层出现 `INTERNAL_ERROR`（Curl error 92），导致 `dnf install` 下载 gcc-c++ 等 RPM 包时失败。这是服务器端或网络中间件的临时故障，属于基础设施问题。PR 新增的 Dockerfile 中 `dnf install` 命令语法和包名均正确，PR 变更不会导致此失败。正确的处理方式是重试 CI 构建。

## 潜在风险
无