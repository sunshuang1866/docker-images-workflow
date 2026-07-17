# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），openEuler 24.03-LTS-SP4 官方软件源 HTTP/2 传输层存在缺陷，导致 dnf 下载 RPM 包时 Curl 报错（error 92），与 PR 代码变更无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确判定失败类型为 `infra-error`，根因是 openEuler 24.03-LTS-SP4 镜像站（`repo.****.org`）的 HTTP/2 服务端返回 `INTERNAL_ERROR (err 2)`，属于服务端协议层缺陷，客户端无法规避。Dockerfile 的 `dnf install` 命令语法和构建逻辑本身正确，无需修改代码。待镜像站恢复后重新触发 CI 即可通过。

## 潜在风险
无