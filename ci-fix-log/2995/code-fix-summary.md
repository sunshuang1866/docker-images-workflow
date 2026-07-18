# 修复摘要

## 修复的问题
无代码修改。本次 CI 失败为 **infra-error（CI 基础设施问题）**，与 PR 代码变更无关。

## 修改的文件
无。无需修改 PR 中的任何文件。

## 修复逻辑
CI 分析报告明确指出：

1. 失败发生在镜像构建和推送全部成功之后的 `[Check]` 阶段。
2. 失败根因是 CI 工具 `eulerpublisher` 内置的 `bwa_test.sh` 测试脚本使用了 Windows 风格行尾（CRLF），导致 shebang 行 `#!/bin/sh` 被解析为 `#!/bin/sh\r`，系统无法找到正确的解释器，报 `bad interpreter: No such file or directory`。
3. 该测试脚本位于 `/usr/etc/eulerpublisher/tests/container/app/bwa_test.sh`，属于 CI 流水线基础设施（`eulerpublisher` 包提供），不在 PR 修改范围内的任何文件中。
4. PR 所有变更文件（`Dockerfile`、`README.md`、`meta.yml`、`image-info.yml`）均不含 CRLF 行尾，也不包含任何测试脚本内容。

**此问题的修复需要 CI 流水线维护方处理**，将 `eulerpublisher` 包中的 `bwa_test.sh` 脚本行尾从 CRLF 转换为 LF。例如在脚本部署阶段执行 `dos2unix` 或 `sed -i 's/\r$//'` 进行批量转换。

## 潜在风险
无。未修改任何代码，不存在引入新问题的风险。