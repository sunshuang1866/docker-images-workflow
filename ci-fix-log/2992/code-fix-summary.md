# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 infra-error，根因是 openEuler 24.03-LTS-SP4 RPM 仓库镜像服务器 HTTP/2 流错误，与 PR 代码无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告判定此次失败为 `infra-error`（CI 基础设施问题）。Dockerfile 中的 `dnf install` 命令语法正确、包名有效，失败原因在于 `repo.***.org`（openEuler RPM 仓库服务器）在处理 HTTP/2 连接时反复出现 `Stream error in the HTTP/2 framing layer: INTERNAL_ERROR (err 2)`，导致 RPM 包下载失败。这是服务器端的临时性网络故障，不影响 Dockerfile 的正确性。建议等待仓库服务恢复后触发 CI 重跑。

## 潜在风险
无