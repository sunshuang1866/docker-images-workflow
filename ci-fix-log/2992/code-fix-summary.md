# 修复摘要

## 修复的问题
无需代码修改。CI 失败由 openEuler 24.03-LTS-SP4 官方包仓库的 HTTP/2 协议临时性故障导致（Curl error 92: Stream error in the HTTP/2 framing layer），与 PR #2992 新增的代码无关。

## 修改的文件
无

## 修复逻辑
CI 失败类型为 `infra-error`，根因是 openEuler 24.03-LTS-SP4 官方仓库在传输大体积 RPM 包（如 gcc、gcc-gfortran）时 HTTP/2 连接异常中断，`dnf` 多次重试后所有镜像均失败。PR 代码仅新增了 Dockerfile 及元数据文件，未引入任何网络配置或自定义仓库，失败与代码变更无关。建议重新触发 CI 构建，等待仓库侧 HTTP/2 服务恢复。

## 潜在风险
无