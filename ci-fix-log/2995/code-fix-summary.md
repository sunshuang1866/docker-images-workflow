# 修复摘要

## 修复的问题
CI 失败为基础设施问题（infra-error），`eulerpublisher` 包内置的 `bwa_test.sh` 测试脚本含有 Windows 换行符（CRLF），导致 `bad interpreter` 错误。与 PR 变更无关，无需修改本 PR 的任何文件。

## 修改的文件
无

## 修复逻辑
CI 分析报告明确指出：此问题根因在于 `eulerpublisher` 包中的 `tests/container/app/bwa_test.sh` 文件行尾序列为 CRLF，需在 `eulerpublisher` 源码仓库中将该文件转换为 LF 并重新发布包。Docker 构建和推送阶段均已成功完成，PR 变更仅涉及新增 Dockerfile、README 和元数据文件，不影响该测试脚本。本 PR 没有需要修改的代码。

## 潜在风险
无