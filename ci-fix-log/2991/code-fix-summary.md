# 修复摘要

## 修复的问题
无需代码修复。CI 失败为 infra-error 类型，由 openEuler 软件源服务器 `repo.openeuler.org` 在 aarch64 架构上出现 HTTP/2 流层瞬时故障（Curl error 92: INTERNAL_ERROR）导致 `dnf install` 下载 guile 等 RPM 包失败。该失败与 PR #2991 的代码变更无关。

## 修改的文件
无（infra-error，无需代码修改）

## 修复逻辑
CI 分析报告确认失败类型为 infra-error，置信度为高。PR 变更仅添加了 vvenc 1.14.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件，Dockerfile 中的 `dnf install -y git gcc gcc-c++ make cmake` 命令语法正确、包名有效。失败根因是软件源服务器端的 HTTP/2 协议故障，属于 CI 基础设施/网络瞬时故障。重新触发 CI 构建即可通过。

## 潜在风险
无