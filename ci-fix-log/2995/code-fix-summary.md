# 修复摘要

## 修复的问题
CI 失败为基础设施错误（infra-error），无需修改本 PR 的任何代码文件。失败原因是 `eulerpublisher` CI 包内自带的 `bwa_test.sh` 测试脚本使用了 Windows 换行符（CRLF），导致 shebang 行 `/bin/sh` 末尾携带不可见的回车符 `^M`，系统无法找到 `/bin/sh^M` 解释器而报 `bad interpreter` 错误。

## 修改的文件
无代码修改。

## 修复逻辑
分析报告明确指出根因在 CI 基础设施文件 `eulerpublisher/tests/container/app/bwa_test.sh` 的换行符问题，与 PR #2995 所提交的 Dockerfile 和元数据文件完全无关。Docker 镜像的构建和推送均正常完成。此问题需要 `eulerpublisher` 包维护人员在包仓库中将 `bwa_test.sh` 的换行符从 CRLF 转换为 LF（通过 `dos2unix` 或编辑器设置），或由 CI runner 管理员在 runner 上执行一次 `dos2unix` 修复。

## 潜在风险
无——未对任何源代码文件进行修改。