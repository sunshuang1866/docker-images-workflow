# 修复摘要

## 修复的问题
无需代码修改 — 该失败为 CI 基础设施问题（infra-error），非代码缺陷。

## 修改的文件
无

## 修复逻辑
CI 失败根因是 openEuler 24.03-LTS-SP4 官方仓库镜像（`repo.****.org`）在构建时出现 HTTP/2 流层协议错误（Curl error 92: INTERNAL_ERROR），导致 `gcc-c++` 等 RPM 包下载失败。PR 新增的 Dockerfile 及 `dnf install` 命令语法和内容完全正确，与失败无关。此类镜像站瞬时故障具有自愈性，重试 CI 即可。

## 潜在风险
无