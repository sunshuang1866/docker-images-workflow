# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施问题（infra-error），非本仓库代码导致。

## 修改的文件
无。未修改任何文件。

## 修复逻辑
CI 分析报告明确指出：

- **失败类型**：infra-error（基础设施错误）
- **根因**：eulerpublisher CI 工具中的 `bwa_test.sh` 测试脚本使用了 Windows 风格换行符（CRLF），导致 shebang 行 `#!/bin/sh` 末尾多出回车符 `\r`（`^M`），系统尝试以 `/bin/sh\r` 作为解释器执行而失败。
- **与 PR 的关联**：无关。PR #2995 新增的 Dockerfile 构建完全成功，镜像导出和推送均正常完成。失败发生在 CI 流水线的 `[Check]` 阶段，由 eulerpublisher 基础设施脚本自身的格式问题触发。

修复需要在 **eulerpublisher 仓库**中对 `tests/container/app/bwa_test.sh` 进行换行符转换（CRLF → LF），而非本仓库。

## 潜在风险
无。本仓库无代码变更。