# 修复摘要

## 修复的问题
无需代码修改。此 CI 失败为 **infra-error**（基础设施错误），与 PR #2980 新增的代码无关。

## 修改的文件
无（infra-error，不需要修改任何源代码文件）

## 修复逻辑
CI 失败的直接原因是 openEuler 24.03-LTS-SP4 官方软件仓库镜像在构建期间出现 HTTP/2 传输层间歇性故障（Curl error 92: INTERNAL_ERROR），导致 gcc-c++ 等 RPM 包下载失败，最终 dnf 安装步骤退出码为 1。

分析确认：
- Dockerfile 中的 `dnf install -y` 命令语法正确
- 所有列出的包名有效（cmake-data、git-core 经重试后成功下载）
- 构建逻辑合理，与 PR 变更内容无关
- 日志中多个不同 RPM 包在不同 HTTP/2 stream 上均出现同类错误，排除包自身问题

建议操作：
1. 等待 openEuler 仓库镜像恢复稳定后，在 CI 中重试（re-trigger）该 job
2. 若该仓库镜像持续不稳定，可考虑在 Dockerfile 的 `dnf install` 命令中增加 `--retries 5` 或 `--setopt=retries=5` 参数

## 潜在风险
无