# 修复摘要

## 修复的问题
无需代码修改。CI 失败为 **infra-error**，与 PR 代码无关。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告明确指出：
- 失败类型为 **infra-error**，置信度高
- 失败根因：CI 基础设施 `eulerpublisher` 包中的 `bwa_test.sh` 测试脚本包含 Windows 风格的 CRLF 换行符（`\r\n`），导致 shebang `#!/bin/sh\r` 被解释为 `/bin/sh\r`，该路径不存在，测试脚本无法执行
- 与 PR 变更**无关**：PR 仅修改了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile`、`HPC/bwa/README.md`、`HPC/bwa/doc/image-info.yml`、`HPC/bwa/meta.yml`，不涉及 CI 基础设施；Docker 镜像构建和推送阶段均成功
- 报告结论：**PR 代码本身无需任何修改**

该问题需要 CI 运维团队将 `eulerpublisher` 包中的 `bwa_test.sh`（及相关 `*_test.sh` 文件）的换行符从 CRLF 转换为 LF，或在 CI 镜像构建流程中增加换行符规范化步骤。

## 潜在风险
无（未修改任何代码）