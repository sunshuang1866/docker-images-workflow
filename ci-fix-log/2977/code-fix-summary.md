# 修复摘要

## 修复的问题
基础设施错误（infra-error），无需代码修改。

## 修改的文件
无。

## 修复逻辑
CI 失败由 `repo.openeuler.org` 在 aarch64 构建节点上发生间歇性 HTTP/2 网络故障导致（Curl error 92: HTTP/2 stream INTERNAL_ERROR；Curl error 56: SSL read failure）。失败根因与 PR #2977 的代码变更无关，Dockerfile 本身没有语法或逻辑问题。属于 CI 基础设施问题，建议等待镜像站网络恢复后重新触发 CI 构建（re-run）。

## 潜在风险
无。