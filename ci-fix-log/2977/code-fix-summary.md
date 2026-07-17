# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error，根因是 `repo.openeuler.org` 镜像站在构建时刻的 HTTP/2 传输不稳定（Curl error 92/56），与 PR 代码变更无关。

## 修改的文件
无（infra-error，无需修改任何文件）

## 修复逻辑
分析报告明确指出：Dockerfile 的 `yum install` 命令语法正确、包名有效，失败完全由 openEuler 官方仓库 `repo.openeuler.org` 在 aarch64 构建时的 HTTP/2 流错误（`INTERNAL_ERROR`）和 SSL 读错误（`SSL_ERROR_SYSCALL`）导致。虽然大部分 RPM 包通过 yum 内置重试成功下载，但传递依赖 `vim-common` 耗尽所有镜像重试次数后永久失败。

建议处理方式：触发 CI 重新构建，同一 Dockerfile 在仓库网络正常时大概率能通过。

## 潜在风险
无