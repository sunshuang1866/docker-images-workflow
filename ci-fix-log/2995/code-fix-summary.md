# 修复摘要

## 修复的问题
无需代码修改 — CI 失败为 infra-error，根因是 CI 基础设施中的测试脚本 `bwa_test.sh` 存在 CRLF 行尾问题，与 PR 变更无关。

## 修改的文件
无（未修改任何源文件）

## 修复逻辑
CI 分析报告明确指出：
- Docker 镜像构建和推送均已成功完成（`[Build] finished`、`[Push] finished`）
- 失败发生在 CI 管线的 `[Check]` 阶段，错误为 `/bin/sh^M: bad interpreter: No such file or directory`
- 根因是 eulerpublisher 系统包中预置的 `bwa_test.sh` 测试脚本使用 Windows 风格 CRLF 行尾，导致 shebang 行被错误解析
- 此为 CI 基础设施（eulerpublisher 包或 CI 测试脚本仓库）的配置问题，与 PR #2995 中新增的 Dockerfile 及元数据文件无关

修复应在 CI 基础设施侧进行：对 `bwa_test.sh` 执行 `dos2unix` 或 `sed -i 's/\r$//'` 转换行尾，或在对应仓库的 `.gitattributes` 中添加 `*.sh text eol=lf`。

## 潜在风险
无