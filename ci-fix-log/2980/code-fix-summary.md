# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施错误（infra-error），由 openEuler RPM 镜像站 HTTP/2 流传输不稳定导致 `dnf install` 下载 `gcc-c++` 等包时 Curl error 92 超时失败。

## 修改的文件
无。

## 修复逻辑
CI 分析报告确认该失败与 PR #2980 的代码变更完全无关。Dockerfile 中的 `dnf install` 包列表均为合法且有效的包名，构建配置无误。失败原因是 CI 构建环境连接 openEuler 24.03-LTS-SP4 镜像仓库时遭遇 HTTP/2 协议层流错误（INTERNAL_ERROR），属于临时性网络故障。应在 openEuler 镜像站恢复稳定后触发 CI 重试。

## 潜在风险
无。