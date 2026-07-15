# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），由 openEuler 24.03-LTS-SP4 上游 RPM 仓库的 HTTP/2 协议层间歇性故障导致。

## 修改的文件
无。所有 PR 变更文件无需修改。

## 修复逻辑
CI 失败日志显示 `Curl error (92): Stream error in the HTTP/2 framing layer`，多个 RPM 包（gcc、gcc-gfortran、glibc-devel、guile）在下载时均遭遇相同的 HTTP/2 stream 错误，部分包在重试后成功下载，表明这是上游 repo 服务器的间歇性问题。Dockerfile 中的 `dnf install` 命令语法正确，包名有效，与 PR 代码变更无关。根据分析报告判定，此为 infra-error，应触发 CI 重试而非修改代码。

## 潜在风险
无