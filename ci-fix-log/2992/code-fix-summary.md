# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施错误（infra-error），由 openEuler 24.03-LTS-SP4 软件仓库（`repo.****.org`）的 HTTP/2 帧层流中断导致 `dnf install` 下载 RPM 包失败。

## 修改的文件
无。PR 变更本身正确，Dockerfile 的 `dnf install` 命令写法与同项目其他已成功的 Dockerfile 一致。

## 修复逻辑
CI 失败分析报告明确指出：
- 失败类型为 `infra-error`，置信度高
- 根因是 openEuler 24.03-LTS-SP4 上游仓库在处理 HTTP/2 请求时反复出现 `Curl error (92): Stream error in the HTTP/2 framing layer`，属于服务端瞬时网络问题
- PR 变更与本次失败**无关**，Dockerfile 内容和格式均正确
- 修复方向为"重试 CI 构建"，等待仓库恢复后重新触发 CI pipeline 即可通过

根据指导原则，infra-error 不进行代码修改。

## 潜在风险
无