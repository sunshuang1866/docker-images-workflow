# 修复摘要

## 修复的问题
CI 构建失败属于基础设施问题（infra-error），非代码问题，无需代码修改。

## 修改的文件
无（infra-error，不需要修改任何源代码文件）。

## 修复逻辑
CI 失败根因为 aarch64 runner 在执行 `dnf install` 从 `repo.openeuler.org` 下载 RPM 包时，遭遇 HTTP/2 流错误（Curl error 92: INTERNAL_ERROR），多个包（git-core、gcc-c++、guile）下载失败，最终导致构建中断。该错误是 CI 构建节点与 openEuler 官方仓库之间的临时性网络/协议层问题，与 PR #2991 新增的 Dockerfile 及元数据文件无关。

Dockerfile 中 `dnf install -y git gcc gcc-c++ make cmake` 命令语法正确、包名有效，无需修改。

**建议操作**: 在 Jenkins 中重新触发 CI 构建，该临时性网络问题大概率已恢复。

## 潜在风险
无