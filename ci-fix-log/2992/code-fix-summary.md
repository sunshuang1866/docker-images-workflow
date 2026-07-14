# 修复摘要

## 修复的问题
无需代码修复。CI 构建失败根因是 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），发生在 `dnf install` 从 openEuler 24.03-LTS-SP4 官方 repo 下载 RPM 包时，属于 CI 基础设施/网络问题，与 PR 代码变更无关。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 失败分析报告判定失败类型为 `infra-error`，置信度高。失败发生在 Dockerfile 第 7-10 行的 `dnf install` 阶段，直接原因是 CI 构建节点与 openEuler 镜像站之间的 HTTP/2 协议层通信中断（多次 Curl error 92: INTERNAL_ERROR，所有镜像源重试均失败）。Dockerfile 中 `dnf install` 的包列表和语法均正确无误，PR 仅新增了该文件，不包含导致此问题的代码缺陷。

建议操作：重试 CI 构建；若持续失败，需排查 CI 构建节点到 openEuler 镜像站的网络链路。

## 潜在风险
无