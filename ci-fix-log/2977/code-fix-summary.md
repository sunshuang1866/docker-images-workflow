# 修复摘要

## 修复的问题
CI 基础设施临时故障 — 无需代码修改。

## 修改的文件
无。

## 修复逻辑
CI 失败原因为 `repo.openeuler.org` 在 aarch64 runner 上发生 HTTP/2 流错误（Curl error (92): INTERNAL_ERROR），导致 `vim-common` RPM 包下载失败，`yum install` 返回 exit code 1。此错误与 PR #2977 的代码变更无关，PR 仅新增了 brpc 1.16.0 在 openEuler 24.03-LTS-SP4 上的 Dockerfile 及配套元数据文件，Dockerfile 语法正确。该失败属于 openEuler 官方仓库的临时网络/HTTP/2 协议故障，属于 CI 基础设施问题（infra-error），无需代码层面的修复。建议重新触发 CI 构建即可恢复。

## 潜在风险
无。