# 修复摘要

## 修复的问题
CI 基础设施故障：aarch64 runner 从 `repo.openeuler.org` 下载 RPM 包时遇到 HTTP/2 传输层错误（Curl error 92/56），属间歇性网络波动，无需代码修改。

## 修改的文件
无（infra-error，不涉及代码修复）

## 修复逻辑
CI 失败分析报告将该失败定性为 `infra-error`，置信度为高。失败原因是 CI aarch64 runner（`ecs-build-docker-aarch64-04-sp`）与 `repo.openeuler.org` 之间的 HTTP/2 传输层中断（`INTERNAL_ERROR` / `SSL_ERROR_SYSCALL`），导致 `vim-common` 等 4 个 RPM 包下载失败。172 个包成功下载，仅 4 个包因间歇性网络问题失败。

Dockerfile 中声明的所有包名（gcc、cmake、protobuf-devel 等）均正确有效，Dockerfile 语法无误，与 PR 改动无关。根据指令，infra-error 不应强行修改代码，建议触发 CI 重试。

## 潜在风险
无