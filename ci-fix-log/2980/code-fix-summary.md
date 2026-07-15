# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为基础设施问题（infra-error），openEuler 24.03-LTS-SP4 仓库镜像 HTTP/2 传输层间歇性故障导致 `gcc-c++` 等 RPM 包下载失败。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定失败类型为 `infra-error`，根因是 openEuler 仓库镜像站在构建时段出现 HTTP/2 `INTERNAL_ERROR` (`Curl error 92`)，属于外部基础设施暂时性故障，与 PR #2980 新增的 Dockerfile 代码无关。Dockerfile 本身语法正确、包名有效、安装命令格式规范。

建议直接重试 CI 构建，等待仓库镜像恢复后即可通过。若该问题频繁复现，可考虑在 Dockerfile 的 `dnf install` 前添加 `echo "http2=false" >> /etc/dnf/dnf.conf` 强制使用 HTTP/1.1。

## 潜在风险
无