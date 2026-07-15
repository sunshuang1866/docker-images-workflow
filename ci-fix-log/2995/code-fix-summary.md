# 修复摘要

## 修复的问题
无需代码修改。CI 失败属于基础设施错误（infra-error），与 PR 代码无关。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：失败发生在 `eulerpublisher` CI 工具的 `[Check]` 阶段，根因是 `bwa_test.sh` 测试脚本的 shebang 行携带 Windows 换行符 `\r`（CRLF），导致解释器路径被误读为 `/bin/sh\r`。该脚本位于 `/usr/etc/eulerpublisher/tests/container/app/`，由 pip 安装的 eulerpublisher 包提供，不在 PR 变更范围内。

PR 的 Docker 构建与推送阶段均成功完成，四个变更文件（Dockerfile、README.md、image-info.yml、meta.yml）无任何问题。

此问题需由 eulerpublisher 维护方或 CI 基础设施管理员修复：
- 将 `bwa_test.sh` 的行尾从 CRLF 转换为 LF（`dos2unix` 或 `sed -i 's/\r$//'`）
- 或排查 CI runner 的 git `core.autocrlf` 配置

## 潜在风险
无（未修改任何代码）