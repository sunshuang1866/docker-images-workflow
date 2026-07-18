# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 infra-error：openEuler 软件仓库（repo.openeuler.org）在 aarch64 构建节点上的临时网络抖动（HTTP/2 流中断、SSL 连接异常），导致 `vim-common` 等包下载失败。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出失败类型为 `infra-error`，置信度高，根因是 `repo.openeuler.org` 在 aarch64 架构上的偶发性网络/服务不稳定，与 PR #2977 的代码变更无关。PR 变更仅新增了符合仓库规范的 brpc Dockerfile、README、image-info.yml 和 meta.yml，Dockerfile 中的 yum install 包名和语法均正确。

修复方向：重新触发 CI 构建（retry），不修改任何源代码。如果多次重试仍失败，可考虑在 Dockerfile 的 yum install 中添加 `--retries 10` 参数作为兜底手段（当前非必需）。

## 潜在风险
无