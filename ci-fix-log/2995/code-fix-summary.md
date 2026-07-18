# 修复摘要

## 修复的问题
无需代码修改 — 本次 CI 失败为基础设施问题（infra-error），根因是 CI 系统中 `eulerpublisher` 测试脚本 `bwa_test.sh` 包含 Windows CRLF 行尾，与 PR #2995 的代码变更无关。

## 修改的文件
无（PR 代码本身无任何问题，Docker 构建和推送阶段均已成功）

## 修复逻辑
CI 失败分析报告明确指出：
- 失败类型为 `infra-error`（置信度：高）
- 根因是 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 脚本的 shebang 行因 CRLF（`\r\n`）被解析为 `#!/bin/sh^M`，导致 `/bin/sh` 无法识别解释器路径
- 该文件属于 CI 基础设施（`eulerpublisher` 包），不在当前仓库中，也不在 PR 变更文件范围内
- PR 的 Docker 镜像构建和推送阶段均成功完成，仅后置 `[Check]` 阶段因基础设施脚本行尾格式问题报错

修复方向：应由 CI 基础设施维护方将 `bwa_test.sh` 的行尾格式从 CRLF 转换为 LF，或在 CI 流水线中执行 `sed -i 's/\r$//'` 预处理。此修复不在当前 PR 范围内。

## 潜在风险
无 — 未对代码做任何修改，Docker 镜像本身构建和功能均正常。