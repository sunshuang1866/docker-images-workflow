# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error），无需代码修改。

## 修改的文件
无

## 修复逻辑
CI 失败分析报告判定失败类型为 `infra-error`，根因是 CI 编排工具 eulerpublisher 安装包中内置的 `bwa_test.sh` 测试脚本含有 Windows 风格 CRLF 行尾（`\r\n`），其 shebang 行 `#!/bin/sh\r` 被系统解析为查找 `/bin/sh\r` 解释器，导致 `bad interpreter: No such file or directory` 错误。Docker 镜像的构建（Build）和推送（Push）阶段均已成功完成，失败仅发生在 eulerpublisher 的 Check 测试执行阶段。

此次 PR 仅新增了 `HPC/bwa/0.7.18/24.03-lts-sp4/Dockerfile` 及更新了 README.md、image-info.yml、meta.yml 等文档文件，均为纯文本，不涉及任何测试脚本。该问题与 PR 代码变更完全无关，属于 CI 基础设施缺陷，Code Fixer 无需也无法通过修改 PR 源文件来解决。

修复应由 CI 运维侧执行：对 eulerpublisher 安装包中的 `bwa_test.sh` 执行 `dos2unix` 或 `sed -i 's/\r$//'` 转换行尾，确保 shebang 行不含回车符。

## 潜在风险
无（未修改任何代码文件）