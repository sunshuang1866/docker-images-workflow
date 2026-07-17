# 修复摘要

## 修复的问题
无需代码修改。CI 失败是 openEuler 24.03-LTS-SP4 仓库镜像站的 HTTP/2 流错误导致的瞬时基础设施故障，与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出失败类型为 `infra-error`，根因是 openEuler 24.03-LTS-SP4 软件仓库镜像站在 HTTP/2 协议层面出现间歇性流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），导致 `gcc-c++` 等 RPM 包下载失败。Dockerfile 中的 `dnf install` 命令语法正确，包名有效，PR 变更完全合理。

按照修复规则，`infra-error` 类型失败不应进行代码级修改。建议重新触发 CI 构建，等待镜像站恢复后重试即可。

## 潜在风险
无