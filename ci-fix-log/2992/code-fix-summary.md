# 修复摘要

## 修复的问题
CI 基础设施瞬时故障，无需代码修复。

## 修改的文件
无

## 修复逻辑
CI 失败类型为 `infra-error`。失败原因是 openEuler 24.03-LTS-SP4 仓库镜像（`repo.****.org`）在通过 HTTPS/HTTP2 传输 RPM 包时出现 `Curl error (92): Stream error in the HTTP/2 framing layer` 错误，属于 CI 构建环境与镜像仓库之间的网络/协议层瞬时故障。Dockerfile 中的 `dnf install` 命令语法正确、包名合法，与 PR 变更无关。建议触发 CI 重新运行（retry），等待仓库镜像服务恢复正常后即可通过。

## 潜在风险
无