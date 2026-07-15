# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：openEuler 24.03-LTS-SP4 软件仓库镜像在 HTTP/2 协议层出现间歇性流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致 `gcc-c++` RPM 包下载失败，与 PR 新增的 Dockerfile 代码无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出此失败与 PR 变更无关。Dockerfile 中的 `dnf install` 命令语法正确，所列包名和版本均有效。日志中 cmake-data 和 git-core 在遭遇同样的 HTTP/2 流错误后因重试成功而通过，`gcc-c++` 仅因在该轮次未遇到成功的镜像而最终失败。根因是 openEuler 仓库镜像侧的 HTTP/2 协议问题，属于 CI 基础设施问题，不需要修改源代码。建议重试 CI 观察是否能通过。

## 潜在风险
无