# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error）：`eulerpublisher` 包中的 `bwa_test.sh` 测试脚本包含 Windows 风格行尾（CRLF），导致 shebang 行解析失败（`/bin/sh^M: bad interpreter`）。

## 修改的文件
无（无需修改 PR 代码）

## 修复逻辑
CI 分析报告明确指出失败类型为 `infra-error`，与本次 PR 的代码变更**完全无关**：
- Docker 镜像构建和推送均成功完成
- 失败仅发生在 CI 框架的 `[Check]` 后处理阶段，该阶段调用了 `eulerpublisher` Python 包中预置的 `bwa_test.sh`，该脚本本身携带 CRLF 行尾
- 此问题需由 CI 基础设施维护者对 `eulerpublisher` 包执行行尾转换（dos2unix / sed），或检查 CI runner 的 `core.autocrlf` 配置

## 潜在风险
无（无代码修改）