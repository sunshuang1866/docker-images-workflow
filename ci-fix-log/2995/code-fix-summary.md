# 修复摘要

## 修复的问题
CI 基础设施错误（infra-error）：eulerpublisher 测试框架中的 `bwa_test.sh` 脚本使用 CRLF 换行符，导致 shebang 行解析失败。无需对本次 PR 的任何代码文件进行修改。

## 修改的文件
无。本次 CI 失败属于基础设施侧问题（eulerpublisher Python 包内的测试脚本换行符错误），不在当前 PR 变更范围内。

## 修复逻辑
CI 分析报告确认：
- Docker 构建完全成功（`[Build] finished`、`[Push] finished`）
- 镜像已成功构建并推送至 `docker.io/****test/bwa:0.7.18-oe2403sp4-x86_64`
- 失败发生在 [Check] 测试阶段，报错 `/bin/sh^M: bad interpreter`，根因是 eulerpublisher 包内 `/etc/eulerpublisher/tests/container/app/bwa_test.sh` 文件以 DOS 换行符（CRLF）保存
- 该测试脚本由 CI 框架控制，**完全不由本次 PR 的代码控制**，无法通过修改 PR 文件解决

此问题需由 eulerpublisher 维护者将 `bwa_test.sh` 的换行符从 CRLF 转换为 LF 后重新发布 Python 包。

## 潜在风险
无。本次未修改任何代码文件，无引入新问题的风险。