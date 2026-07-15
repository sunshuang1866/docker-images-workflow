# 修复摘要

## 修复的问题
infra-error — 无需代码修改。CI 失败根因是 eulerpublisher 测试脚本 `bwa_test.sh` 包含 Windows 风格换行符（CRLF），导致 shebang 解析异常（`bad interpreter`），与本次 PR 的代码变更无关。

## 修改的文件
无（infra-error，不涉及源码修改）。

## 修复逻辑
CI 失败分析报告明确指出：
1. Docker 镜像构建和推送均已成功完成（Build/Push 阶段通过）。
2. 失败仅发生在 eulerpublisher 的 Check 阶段，错误为 `/bin/sh^M: bad interpreter`，是测试脚本的换行符（CRLF）导致。
3. 根因在 CI 基础设施（eulerpublisher 仓库中的测试脚本），与 PR #2995 的代码变更完全无关。PR 新增的 Dockerfile、README.md、image-info.yml、meta.yml 均为正确的镜像元数据和构建逻辑。
4. 根据修复原则，`infra-error` 不应强行修改源码。此问题需由 CI 维护方对 eulerpublisher 仓库中的 `tests/container/app/bwa_test.sh` 执行 `dos2unix` 或 `sed -i 's/\r$//'` 转换换行符为 LF 后重新部署。

## 潜在风险
无。