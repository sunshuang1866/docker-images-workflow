# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 `infra-error`——`repo.openeuler.org` 镜像站在 aarch64 架构上返回 HTTP/2 流错误（`INTERNAL_ERROR`），导致 `dnf install` 下载 RPM 包失败。

## 修改的文件
无

## 修复逻辑
CI 分析报告判定此失败为  **infra-error**（置信度: 高），与 PR #2991 的代码变更无关。PR 仅新增了一个标准 Dockerfile（安装编译工具链后构建 vvenc）及元数据文件，Dockerfile 自身的语法和构建逻辑均无问题。

失败的直接原因是 openEuler 官方镜像站 `repo.openeuler.org` 在 SP4 aarch64 仓库上返回 HTTP/2 帧层流错误（`Curl error (92)`），导致 `git-core`、`gcc-c++`、`guile` 等多个包下载失败。这属于上游仓库的临时服务端问题，应通过重试 CI 解决，不应修改代码。

## 潜在风险
无